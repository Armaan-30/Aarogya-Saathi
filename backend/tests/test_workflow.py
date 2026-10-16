import io
import json
import pytest
from types import SimpleNamespace
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic import ValidationError
from app.main import app, get_current_user
from app.db import Base, get_db, User
from app.schemas import Analysis
from app.config import ROOT
from app.services.document_extractor import extract, MAX_SIZE, ocr_available
from app.services.safety import validate_grounding
from app import config

@pytest.fixture
def client(tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "test.db"}', connect_args={'check_same_thread':False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine)
    def override():
        with Session() as s: yield s
    with Session() as s:
        test_user=User(id='test-owner',email='test-owner@example.invalid',password_hash='unused')
        s.add(test_user); s.commit()
        test_user_id, test_user_email = test_user.id, test_user.email
    app.dependency_overrides[get_db] = override
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=test_user_id, email=test_user_email)
    with TestClient(app) as c: yield c
    app.dependency_overrides.clear()
    engine.dispose()

@pytest.fixture
def auth_client(tmp_path):
    engine=create_engine(f'sqlite:///{tmp_path / "auth-test.db"}', connect_args={'check_same_thread':False})
    Base.metadata.create_all(engine)
    Session=sessionmaker(engine)
    def override():
        with Session() as s: yield s
    app.dependency_overrides[get_db]=override
    app.dependency_overrides.pop(get_current_user, None)
    with TestClient(app) as c: yield c
    app.dependency_overrides.clear()
    engine.dispose()

def data(name): return (ROOT / 'demo/synthetic_documents' / name).read_bytes()

def test_health(client):
    r=client.get('/api/health'); assert r.status_code==200
    assert r.json()['status']=='ok'
    assert 'API_KEY' not in r.text and config.API_KEY not in r.text if config.API_KEY else True

@pytest.mark.parametrize('name', ['clear.pdf','incomplete.pdf'])
def test_pdf_extraction(name):
    text, method=extract(data(name),name)
    assert 'SYNTHETIC HACKATHON DEMO' in text
    assert method=='PDF text'

@pytest.mark.parametrize('name', ['scanned.png','scanned.jpg','scanned.pdf'])
def test_real_ocr(name):
    if not ocr_available(): pytest.skip('Tesseract not installed')
    text, method=extract(data(name),name)
    assert 'Tesseract OCR' in method and 'DemoMed A' in text

@pytest.mark.parametrize('name,body', [('bad.pdf',b'not a pdf'),('bad.png',b'<script>alert(1)</script>'),('bad.exe',b'MZ'),('bad.jpg',None)])
def test_invalid_uploads(client,name,body):
    r=client.post('/api/documents/analyze',files={'file':(name,body or data('scanned.png'))})
    assert r.status_code in (415,422)

def test_oversize(client):
    r=client.post('/api/documents/analyze',files={'file':('large.pdf',b'%PDF-'+b'a'*MAX_SIZE)})
    assert r.status_code==413

def test_empty_pdf():
    import fitz
    pdf=fitz.open();pdf.new_page()
    with pytest.raises(HTTPException) as e: extract(pdf.tobytes(),'empty.pdf')
    assert e.value.status_code in (422,503)

def test_schema():
    with pytest.raises(ValidationError): Analysis.model_validate({'summary':'Missing items'})

def test_grounding():
    result=Analysis(document_type='test',summary='Test',items=[{'id':'1','kind':'medicine','title':'Medicine','wording':'Take 99 tablets','source':'Medicine: twice daily.','frequency':'twice daily','dosage':'99 tablets'}])
    out=validate_grounding(result,'Medicine: twice daily.')
    assert out.items[0].uncertain
    assert any('Dosage' in x for x in out.items[0].concerns)

def test_fabricated_evidence():
    result=Analysis(document_type='test',summary='Test',items=[{'id':'1','kind':'instruction','title':'Rest','wording':'Rest','source':'Rest'}])
    assert validate_grounding(result,'Unrelated source text').items[0].uncertain

def test_duplicate_medicine_blocked():
    values={'kind':'medicine','title':'A','wording':'A 1 tablet daily for 2 days','source':'A 1 tablet daily for 2 days','dosage':'1 tablet','frequency':'daily','duration':'for 2 days'}
    result=Analysis(document_type='test',summary='Test',items=[dict(id='1',**values),dict(id='2',**values)])
    assert all(i.uncertain for i in validate_grounding(result,values['source']).items)

def test_complete_demo_journey(client):
    doc=client.post('/api/demo/cases/clear/analyze',json={'mode':'demo'}).json()
    assert doc['mode']=='demo' and not any(i['uncertain'] for i in doc['analysis']['items'])
    id=doc['id']; assert client.get(f'/api/documents/{id}').json()['id']==id
    assert client.post(f'/api/documents/{id}/verify',json={'decisions':{}}).status_code==422
    decisions={i['id']:'reviewed' for i in doc['analysis']['items']}
    r=client.post(f'/api/documents/{id}/verify',json={'decisions':decisions})
    assert r.status_code==200
    plan_id=r.json()['plan_id']
    assert client.post(f'/api/documents/{id}/verify',json={'decisions':decisions}).json()['plan_id']==plan_id
    plan=client.get(f'/api/care-plans/{plan_id}').json()
    assert len(plan['tasks'])==4
    task_id=plan['tasks'][0]['id']
    assert client.patch(f'/api/care-plans/{plan_id}/tasks/{task_id}',json={'completed':True}).status_code==200
    assert client.get(f'/api/care-plans/{plan_id}').json()['tasks'][0]['completed'] is True
    assert client.patch(f'/api/care-plans/wrong/tasks/{task_id}',json={'completed':True}).status_code==404
    for lang in ('hi','mr','en'):
        tr=client.post(f'/api/documents/{id}/translate',json={'language':lang})
        assert tr.status_code==200 and tr.json()['explanation']

def test_uncertain_medicine_never_becomes_task(client):
    doc=client.post('/api/demo/cases/incomplete/analyze',json={'mode':'demo'}).json()
    decisions={i['id']:'reviewed' for i in doc['analysis']['items']}
    assert client.post(f'/api/documents/{doc["id"]}/verify',json={'decisions':decisions}).status_code==422
    decisions={i['id']:'clarify' if i['uncertain'] else 'reviewed' for i in doc['analysis']['items']}
    plan_id=client.post(f'/api/documents/{doc["id"]}/verify',json={'decisions':decisions}).json()['plan_id']
    plan=client.get(f'/api/care-plans/{plan_id}').json()
    assert len(plan['clarifications'])==2
    assert all(t['item']['kind']!='medicine' for t in plan['tasks'])

def test_demo_mode_never_substitutes_upload(client,monkeypatch):
    monkeypatch.setattr(config,'DEMO_MODE',True)
    r=client.post('/api/documents/analyze',files={'file':('clear.pdf',data('clear.pdf'))})
    assert r.status_code==503
    assert 'demo mode' in r.json()['detail']

def test_missing_key(client,monkeypatch):
    monkeypatch.setattr(config,'DEMO_MODE',False);monkeypatch.setattr(config,'FREE_TIER',True);monkeypatch.setattr(config,'API_KEY','')
    r=client.post('/api/documents/analyze',files={'file':('clear.pdf',data('clear.pdf'))})
    assert r.status_code==503 and 'key is missing' in r.json()['detail']

def test_missing_record(client): assert client.get('/api/documents/missing').status_code==404

def test_ocr_missing(monkeypatch):
    from app.services import document_extractor
    monkeypatch.setattr(document_extractor,'ocr_available',lambda:False)
    with pytest.raises(HTTPException) as e: extract(data('scanned.png'),'scanned.png')
    assert e.value.status_code==503

def test_upload_persists_original_and_live_label(client,monkeypatch):
    from app import main
    result=Analysis.model_validate_json((ROOT/'demo/expected_outputs/clear.json').read_text())
    monkeypatch.setattr(main,'analyze',lambda text:validate_grounding(result,text))
    response=client.post('/api/documents/analyze',files={'file':('clear.pdf',data('clear.pdf'),'application/pdf')})
    assert response.status_code==200 and response.json()['mode']=='live'
    original=client.get(f'/api/documents/{response.json()["id"]}/file')
    assert original.content==data('clear.pdf')
    assert original.headers['content-type']=='application/pdf'

def test_free_tier_confirmation_required(client,monkeypatch):
    monkeypatch.setattr(config,'DEMO_MODE',False);monkeypatch.setattr(config,'FREE_TIER',False)
    r=client.post('/api/documents/analyze',files={'file':('clear.pdf',data('clear.pdf'))})
    assert r.status_code==503 and 'free tier' in r.json()['detail']

@pytest.mark.parametrize('status,phrase',[(400,'rejected'),(401,'invalid'),(403,'denied'),(404,'unavailable'),(429,'quota')])
def test_provider_errors_are_readable_and_redacted(client,monkeypatch,status,phrase):
    from app.services import gemini_service
    from google.genai import errors
    monkeypatch.setattr(config,'DEMO_MODE',False);monkeypatch.setattr(config,'FREE_TIER',True)
    def fail(): raise errors.APIError(status,{'error':{'message':'SECRET_PROVIDER_DETAILS'}})
    monkeypatch.setattr(gemini_service,'client',fail)
    r=client.post('/api/documents/analyze',files={'file':('clear.pdf',data('clear.pdf'))})
    assert r.status_code==503 and phrase in r.json()['detail']
    assert 'SECRET_PROVIDER_DETAILS' not in r.text

def test_invalid_ai_json_is_safe(client,monkeypatch):
    from app.services import gemini_service
    monkeypatch.setattr(config,'DEMO_MODE',False);monkeypatch.setattr(config,'FREE_TIER',True)
    def fail(): raise ValueError('SECRET_BAD_RESPONSE')
    monkeypatch.setattr(gemini_service,'client',fail)
    r=client.post('/api/documents/analyze',files={'file':('clear.pdf',data('clear.pdf'))})
    assert r.status_code==502 and 'SECRET_BAD_RESPONSE' not in r.text

def test_translation_rejects_numeric_changes(monkeypatch):
    from types import SimpleNamespace
    from app.services import translation_service
    from app.schemas import Translation
    monkeypatch.setattr(translation_service,'generate',lambda *a:Translation(explanation='Rest for 99 days'))
    doc=SimpleNamespace(mode='live',result={'summary':'Rest for 2 days','items':[]})
    with pytest.raises(HTTPException) as e: translation_service.translate(doc,'hi')
    assert e.value.status_code==502

def test_translation_restores_exact_source_tokens(monkeypatch):
    from types import SimpleNamespace
    from app.services import translation_service
    from app.schemas import Translation
    def translated(prompt, *args):
        assert 'DemoMed A' not in prompt and '08:00' not in prompt
        return Translation(explanation=prompt)
    monkeypatch.setattr(translation_service,'generate',translated)
    original='DemoMed A: 1 tablet at 08:00 for 3 days.'
    doc=SimpleNamespace(mode='live',result={'summary':original,'items':[{'kind':'medicine','title':'DemoMed A'}]})
    assert translation_service.translate(doc,'mr')['explanation']==original

def test_document_chat_requires_source_backed_citations(monkeypatch):
    from app.services import document_chat_service
    from app.schemas import ChatAnswer
    source='Keep the dressing clean and dry. Return to the clinic on 22 October.'
    doc=SimpleNamespace(text=source, filename='uploaded.pdf', result={'summary':'Dressing and follow-up instructions.', 'items':[]})
    monkeypatch.setattr(document_chat_service, 'generate', lambda prompt, *args: ChatAnswer(answer='Keep the dressing dry.', citations=[{'quote':'Keep the dressing clean and dry.'}]))
    assert document_chat_service.ask_document(doc,'What about the dressing?','en',[]) == {
        'answer':'Keep the dressing dry.', 'citations':['Keep the dressing clean and dry.']}
    monkeypatch.setattr(document_chat_service, 'generate', lambda prompt, *args: ChatAnswer(answer='Take two tablets.', citations=[{'quote':'Take two tablets.'}]))
    assert document_chat_service.ask_document(doc,'How much medicine?','en',[]) == {
        'answer':document_chat_service.REFUSAL, 'citations':[]}

def test_document_chat_api_saves_per_document_history_and_handles_missing_doc(client,monkeypatch):
    from app import main
    monkeypatch.setattr(main, 'ask_document', lambda doc, question, language, previous: {
        'answer':'Keep the dressing dry.', 'citations':['Keep the dressing clean and dry.']})
    doc=client.post('/api/demo/cases/clear/analyze',json={'mode':'demo'}).json()
    payload={'document_id':doc['id'],'question':'What about the dressing?','language':'en'}
    response=client.post('/api/chat/document',json=payload)
    assert response.status_code==200
    history=response.json()
    assert history['document_name']==doc['filename']
    assert [m['role'] for m in history['messages']]==['user','assistant']
    assert history['messages'][1]['citations']==['Keep the dressing clean and dry.']
    assert client.get(f"/api/chat/history/{doc['id']}").json()==history
    assert client.get('/api/chat/history/missing').status_code==404

def test_account_signup_hashes_password_and_revokes_http_only_session(auth_client):
    assert auth_client.get('/api/auth/status').json()['setup_required']
    payload={'email':'patient@example.invalid','password':'correct-horse-battery-staple'}
    response=auth_client.post('/api/auth/register',json=payload)
    assert response.status_code==200
    assert 'httponly' in response.headers['set-cookie'].lower()
    assert 'samesite=strict' in response.headers['set-cookie'].lower()
    assert auth_client.get('/api/auth/me').json()['email']=='patient@example.invalid'
    assert auth_client.post('/api/auth/logout').status_code==200
    assert auth_client.get('/api/auth/me').status_code==401

def test_caregiver_requires_invitation_is_scoped_audited_and_revocable(auth_client):
    from app.db import AccessAudit, CareTaskEvent
    patient={'email':'patient@example.invalid','password':'patient-password-long-123'}
    assert auth_client.post('/api/auth/register',json=patient).status_code==200
    doc=auth_client.post('/api/demo/cases/clear/analyze',json={'mode':'demo'}).json()
    decisions={item['id']:'reviewed' for item in doc['analysis']['items']}
    plan_id=auth_client.post(f"/api/documents/{doc['id']}/verify",json={'decisions':decisions}).json()['plan_id']
    caregiver={'email':'helper@example.invalid','password':'helper-password-long-456'}
    assert auth_client.post('/api/auth/register',json=caregiver).status_code==200
    assert auth_client.get(f"/api/documents/{doc['id']}").status_code==404
    assert auth_client.post('/api/auth/logout').status_code==200
    assert auth_client.post('/api/auth/login',json=patient).status_code==200
    invitation=auth_client.post('/api/caregivers/invite',json={'email':caregiver['email'],'can_complete_tasks':True})
    assert invitation.status_code==200
    assert auth_client.post('/api/auth/logout').status_code==200
    assert auth_client.post('/api/auth/login',json=caregiver).status_code==200
    assert auth_client.post('/api/caregivers/accept',json={'invite_code':invitation.json()['invite_code']}).status_code==200
    dashboard=auth_client.get('/api/caregivers/dashboard').json()
    assert len(dashboard['patients'])==1 and dashboard['patients'][0]['plans'][0]['id']==plan_id
    task=dashboard['patients'][0]['plans'][0]['tasks'][0]
    assert auth_client.patch(f"/api/care-plans/{plan_id}/tasks/{task['id']}",json={'completed':True}).status_code==200
    assert auth_client.post('/api/auth/logout').status_code==200
    assert auth_client.post('/api/auth/login',json=patient).status_code==200
    relations=auth_client.get('/api/caregivers').json()
    grant_id=relations['caregivers'][0]['id']
    assert auth_client.delete(f'/api/caregivers/{grant_id}').json()['status']=='revoked'
    assert auth_client.post('/api/auth/logout').status_code==200
    assert auth_client.post('/api/auth/login',json=caregiver).status_code==200
    assert auth_client.get(f"/api/care-plans/{plan_id}").status_code==404

def test_reminder_state_requires_explicit_date_and_time():
    from datetime import datetime
    from app.services.recovery_plan_service import reminder_status, LOCAL_ZONE
    now=datetime(2026,10,15,10,0,tzinfo=LOCAL_ZONE)
    assert reminder_status({'date':'2026-10-15','timing':'13:00'},False,now)['state']=='today'
    assert reminder_status({'date':'2026-10-14','timing':'13:00'},False,now)['state']=='overdue'
    assert reminder_status({'date':'2026-10-16'},False,now)['state']=='date_only'
    assert reminder_status({'timing':'08:00'},False,now)['state']=='unscheduled'
    assert reminder_status({'date':'2026-10-16','timing':'08:00'},True,now)['state']=='completed'
