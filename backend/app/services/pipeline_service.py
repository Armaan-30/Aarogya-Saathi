import hashlib
import json
import re
from threading import Lock
from .. import config
from ..schemas import Analysis, ProcessingInfo
from .document_extractor import validate_file, extract_details
from .gemini_vision_service import transcribe
from .safety import apply_processing_safety

PIPELINE_VERSION = 'hybrid-v1'
_locks = [Lock() for _ in range(64)]

def request_key(data, document_mode, mime, owner_id=''):
    settings = json.dumps([PIPELINE_VERSION, config.MODEL, document_mode, mime, owner_id])
    return hashlib.sha256(settings.encode() + data).hexdigest()

def request_lock(key):
    return _locks[int(key[:8], 16) % len(_locks)]

def process(data, filename, document_mode, analyze):
    if document_mode == 'printed':
        text, method, info = extract_details(data, filename)
    else:
        mime = validate_file(data, filename)
        transcript = transcribe(data, mime)
        text = transcript.text.strip()
        if re.search(r'\[\s*(unreadable|illegible|unclear)\s*\]', text, re.I) and not transcript.unreadable_regions:
            transcript.unreadable_regions.append('Transcription contains unreadable spans; compare with the original image.')
        info = ProcessingInfo(document_mode='handwritten', methods=['Gemini Vision'],
            warnings=transcript.warnings, unreadable_regions=transcript.unreadable_regions,
            vision_model=config.MODEL, image_input_verified=True,
            provenance='AI transcription of the original image. Text matching does not independently verify handwriting. All handwritten medication items require professional verification.')
        method = 'Gemini Vision'
        if not text:
            info.warnings.append('No readable text could be transcribed. Obtain a clearer document or ask the prescribing professional.')
    result = analyze(text) if text else Analysis(document_type='Unreadable handwritten image',
        summary='The image could not be transcribed. No medical instructions were inferred.', items=[])
    return text, method, apply_processing_safety(result, info), info
