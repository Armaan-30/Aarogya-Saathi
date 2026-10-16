from types import SimpleNamespace

from app.services import indian_medicine_info, speech_service


def test_cdsco_lookup_uses_name_and_strength_from_official_table(monkeypatch):
    indian_medicine_info._cache.clear()
    page = '''<table><tr><th>Sr.No</th><th>Drug Name</th><th>Strength</th><th>Indication</th><th>Date</th></tr>
    <tr><td>1</td><td>Paracetamol tablets</td><td>Each tablet contains paracetamol 500 mg</td><td>Approved use A</td><td>01.01.2025</td></tr>
    <tr><td>2</td><td>Paracetamol tablets</td><td>Each tablet contains paracetamol 650 mg</td><td>Approved use B</td><td>01.01.2025</td></tr>
    <tr><td>3</td><td>Other medicine</td><td>100 mg</td><td>Use with paracetamol</td><td>01.01.2025</td></tr></table>'''
    monkeypatch.setattr(indian_medicine_info.httpx, 'get', lambda *a, **k: SimpleNamespace(text=page, raise_for_status=lambda: None))

    result = indian_medicine_info.approved_uses('Paracetamol', '500 mg')

    assert len(result['results']) == 1
    assert result['results'][0]['approved_indication'] == 'Approved use A'
    assert result['results'][0]['strength'].endswith('500 mg')
    assert 'cdscoonline.gov.in' in result['source_url']


def test_cdsco_lookup_does_not_treat_mention_in_indication_as_drug_match(monkeypatch):
    indian_medicine_info._cache.clear()
    page = '''<table><tr><th>Sr.No</th><th>Drug Name</th><th>Strength</th><th>Indication</th><th>Date</th></tr>
    <tr><td>1</td><td>Unrelated product</td><td>10 mg</td><td>May be combined with acetaminophen</td><td>01.01.2025</td></tr></table>'''
    monkeypatch.setattr(indian_medicine_info.httpx, 'get', lambda *a, **k: SimpleNamespace(text=page, raise_for_status=lambda: None))

    assert indian_medicine_info.approved_uses('acetaminophen')['results'] == []


def test_speech_service_uses_only_configured_tts_model_and_returns_wav(monkeypatch):
    called = {}

    class SDK:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        class interactions:
            @staticmethod
            def create(**kwargs):
                called.update(kwargs)
                return SimpleNamespace(output_audio=SimpleNamespace(mime_type='audio/wav', data='c2FtcGxl'))

    monkeypatch.setattr(speech_service, 'require_live', lambda: None)
    monkeypatch.setattr(speech_service, 'client', lambda: SDK())
    result = speech_service.synthesize('नमस्कार.', 'mr')

    assert called['model'] == 'gemini-3.8-flash-lite-tts'
    assert called['input'][0]['content'][0]['text'] == 'नमस्कार.'
    assert result == {'language': 'mr', 'mime_type': 'audio/wav', 'audio_base64': 'c2FtcGxl'}


def test_speech_service_rejects_unsupported_language():
    from fastapi import HTTPException
    import pytest

    with pytest.raises(HTTPException) as error:
        speech_service.synthesize('hello', 'en')
    assert error.value.status_code == 422
