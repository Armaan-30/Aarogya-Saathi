import io
import json
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from PIL import Image
from app import config, main
from app.schemas import Analysis, VisionTranscription, ProcessingInfo
from app.services import pipeline_service, gemini_vision_service, gemini_service, translation_service
from app.services.document_extractor import extract_details, readable
from app.services.image_preprocessor import load_image, prepare_image
from app.services.safety import apply_processing_safety
from app.db import DocumentProcessing, Document
from test_workflow import client, data

@pytest.fixture(autouse=True)
def live_config(monkeypatch):
    monkeypatch.setattr(config, 'DEMO_MODE', False)
    monkeypatch.setattr(config, 'FREE_TIER', True)

def analysis():
    return Analysis.model_validate_json((config.ROOT/'demo/expected_outputs/clear.json').read_text())

def upload(client, name='handwritten.png', mode='handwritten'):
    return client.post('/api/documents/analyze', data={'document_mode':mode}, files={'file':(name,data(name))})

def test_document_mode_validation(client):
    assert upload(client, mode='unknown').status_code == 422
    assert upload(client, name='clear.pdf').status_code == 415

def test_handwritten_demo_is_explicit_and_blocked(client):
    doc=client.post('/api/demo/cases/handwritten/analyze',json={'mode':'demo'}).json()
    assert doc['mode']=='demo'
    assert doc['processing']['image_input_verified'] is False
    assert doc['extraction']=='Gemini Vision (prerecorded)'
    assert all(i['professional_verification_required'] for i in doc['analysis']['items'])
    decisions={i['id']:'reviewed' for i in doc['analysis']['items']}
    assert client.post(f'/api/documents/{doc["id"]}/verify',json={'decisions':decisions}).status_code==422
    decisions={i['id']:'clarify' for i in doc['analysis']['items']}
    plan=client.post(f'/api/documents/{doc["id"]}/verify',json={'decisions':decisions}).json()['plan_id']
    saved=client.get(f'/api/care-plans/{plan}').json()
    assert saved['tasks']==[] and len(saved['clarifications'])==3

def test_blurry_demo_has_no_invented_instructions(client):
    r=client.post('/api/demo/cases/blurry/analyze',json={'mode':'demo'})
    assert r.status_code==200
    doc=r.json()
    assert doc['analysis']['items']==[]
    assert doc['processing']['unreadable_regions']

def test_live_vision_is_original_bytes_then_text_analysis(client,monkeypatch):
    calls=[]
    text='DemoMed A: 1 tablet once daily at 08:00 after breakfast for 3 days.'
    def vision(content,mime):
        assert content==data('handwritten.png') and mime=='image/png'
        calls.append('vision')
        return VisionTranscription(text=text)
    def analyze(value):
        assert value==text
        calls.append('analysis')
        return Analysis(document_type='handwritten',summary='Review instructions.',items=[analysis().items[0]])
    monkeypatch.setattr(pipeline_service,'transcribe',vision)
    monkeypatch.setattr(main,'analyze',analyze)
    doc=upload(client).json()
    assert calls==['vision','analysis']
    assert doc['processing']['image_input_verified'] is True
    assert doc['analysis']['items'][0]['professional_verification_required']
    assert client.get(f'/api/documents/{doc["id"]}/file').content==data('handwritten.png')
    assert client.post(f'/api/documents/{doc["id"]}/verify',json={'decisions':{'med-1':'reviewed'}}).status_code==422

@pytest.mark.parametrize('name', ['handwriting-script.png','handwriting-comic.png','handwriting-cursive.png'])
def test_synthetic_handwriting_style_variants_enter_vision_pipeline(client,monkeypatch,name):
    source=data(name)
    received=[]
    monkeypatch.setattr(pipeline_service,'transcribe',lambda content,mime:(received.append((content,mime)) or VisionTranscription(text='SIMULATED FONT SAMPLE')))
    monkeypatch.setattr(main,'analyze',lambda text:Analysis(document_type='synthetic handwriting lookalike',summary='Review the original image.',items=[]))
    response=client.post('/api/documents/analyze',data={'document_mode':'handwritten'},files={'file':(name,source,'image/png')})
    assert response.status_code==200
    assert received==[(source,'image/png')]
    assert response.json()['processing']['image_input_verified'] is True
    assert response.json()['analysis']['items']==[]

def test_empty_vision_skips_text_generation(client,monkeypatch):
    monkeypatch.setattr(pipeline_service,'transcribe',lambda *a:VisionTranscription(text='',warnings=['Cannot read image']))
    def forbidden(*a): pytest.fail('Empty transcription must not go to text analysis')
    monkeypatch.setattr(main,'analyze',forbidden)
    r=upload(client)
    assert r.status_code==200 and r.json()['analysis']['items']==[]
    assert r.json()['analysis']['uncertainties']

def test_unreadable_markers_survive_analysis(client,monkeypatch):
    monkeypatch.setattr(pipeline_service,'transcribe',lambda *a:VisionTranscription(text='Return on [unreadable] to clinic.'))
    monkeypatch.setattr(main,'analyze',lambda *a:Analysis(document_type='test',summary='Review',items=[dict(id='x',kind='follow_up',title='Visit',source='Return on [unreadable] to clinic.',wording='Return on [unreadable] to clinic.')]))
    doc=upload(client).json()
    assert doc['analysis']['items'][0]['uncertain']

def test_identical_upload_reuses_live_result(client,monkeypatch):
    calls=[]
    monkeypatch.setattr(main,'analyze',lambda text:(calls.append(text) or analysis()))
    a=upload(client,'clear.pdf','printed').json()
    b=upload(client,'clear.pdf','printed').json()
    assert a['id']==b['id'] and not a['reused'] and b['reused']
    assert len(calls)==1 and b['mode']=='live'

def test_concurrent_uploads_coalesce(client,monkeypatch):
    calls=[]
    monkeypatch.setattr(main,'analyze',lambda text:(calls.append(text) or analysis()))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:upload(client,'clear.pdf','printed').json(),range(2)))
    assert len(calls)==1 and results[0]['id']==results[1]['id']

def test_cache_separates_mode_model_and_version(monkeypatch):
    key=pipeline_service.request_key(b'content','printed','image/png')
    assert key!=pipeline_service.request_key(b'content','handwritten','image/png')
    monkeypatch.setattr(config,'MODEL','other')
    assert key!=pipeline_service.request_key(b'content','printed','image/png')
    next_key=pipeline_service.request_key(b'content','printed','image/png')
    monkeypatch.setattr(pipeline_service,'PIPELINE_VERSION','v-next')
    assert next_key!=pipeline_service.request_key(b'content','printed','image/png')

def test_translations_are_reused(client,monkeypatch):
    doc=client.post('/api/demo/cases/clear/analyze',json={'mode':'demo'}).json()
    calls=[]
    monkeypatch.setattr(main,'translate',lambda doc,lang:(calls.append(lang) or {'language':lang,'mode':'demo','explanation':'Stored translation'}))
    for _ in range(2):
        assert client.post(f'/api/documents/{doc["id"]}/translate',json={'language':'hi'}).status_code==200
    assert calls==['hi']

def test_failed_generation_is_not_cached(client,monkeypatch):
    def fail(*a): raise HTTPException(503,'Quota unavailable')
    monkeypatch.setattr(main,'analyze',fail)
    assert upload(client,'clear.pdf','printed').status_code==503
    monkeypatch.setattr(main,'analyze',lambda *a:analysis())
    assert upload(client,'clear.pdf','printed').json()['reused'] is False

def test_vision_unsupported_model_is_readable(monkeypatch):
    from google.genai import errors
    def fail(): raise errors.APIError(400,{'error':{'message':'SECRET unsupported image'}})
    monkeypatch.setattr(gemini_service,'client',fail)
    with pytest.raises(HTTPException) as exc:
        gemini_vision_service.transcribe(data('handwritten.png'),'image/png')
    assert 'image input' in exc.value.detail and 'SECRET' not in exc.value.detail

def test_vision_request_contains_image_part(monkeypatch):
    def generate(prompt,schema,system,**options):
        assert prompt[0].inline_data.data==b'original'
        assert prompt[0].inline_data.mime_type=='image/jpeg'
        assert options['image_input'] is True
        return VisionTranscription(text='Only visible words')
    monkeypatch.setattr(gemini_vision_service,'generate',generate)
    assert gemini_vision_service.transcribe(b'original','image/jpeg').text=='Only visible words'

def test_quality_warning_blocks_every_item():
    result=apply_processing_safety(analysis(),ProcessingInfo(warnings=['Unreadable page']))
    assert all(i.uncertain and i.professional_verification_required for i in result.items)

def test_garbage_embedded_text_is_not_readable():
    assert not readable('???????????????????? ////////')
    assert not readable('� text corrupted ' * 10)
    assert readable('Keep the dressing clean and dry. Rest at home for 2 days.')

def test_preprocessing_preserves_original_and_bounds_dimensions():
    original=Image.new('RGB',(300,200),'white')
    prepared,steps,warnings=prepare_image(original)
    assert original.size==(300,200)
    assert max(prepared.size)<=2600 and warnings
    assert any('resized' in s for s in steps)

def test_mixed_pdf_keeps_both_processing_paths():
    import pymupdf
    pdf=pymupdf.open(stream=data('clear.pdf'),filetype='pdf')
    with pymupdf.open(stream=data('scanned.pdf'),filetype='pdf') as scanned:
        pdf.insert_pdf(scanned)
    text,method,info=extract_details(pdf.tobytes(),'mixed.pdf')
    assert set(info.methods)=={'PyMuPDF','Tesseract OCR'}
    assert text.count('DemoMed A')==2
    pdf.close()
