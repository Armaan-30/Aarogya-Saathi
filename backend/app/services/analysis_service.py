import json
from fastapi import HTTPException
from ..config import ROOT
from ..schemas import Analysis, ProcessingInfo
from .safety import validate_grounding, apply_processing_safety
from .document_extractor import extract_details

CASES = {
    'clear': ('Clear discharge summary', 'Complete instructions, dressing care and a follow-up.', 'clear.pdf'),
    'incomplete': ('Incomplete prescription', 'See how unclear medicine instructions are held for review.', 'incomplete.pdf'),
    'scanned': ('Scanned document', 'An image sample processed with real Tesseract OCR.', 'scanned.png'),
    'handwritten': ('Handwritten prescription', 'Simulated handwriting with deliberately unreadable medicine details.', 'handwritten.png'),
    'blurry': ('Blurry prescription', 'A partially obscured sample that must stay flagged for clarification.', 'blurry.png'),
}

def sample_path(id):
    if id not in CASES: raise HTTPException(404, 'Sample not found.')
    return ROOT / 'demo' / 'synthetic_documents' / CASES[id][2]

def demo_analysis(id):
    path = sample_path(id)
    if id in ('handwritten', 'blurry'):
        fixture = json.loads((ROOT / 'demo' / 'expected_outputs' / f'{id}-transcription.json').read_text(encoding='utf-8'))
        text, method = fixture['text'], 'Gemini Vision (prerecorded)'
        info = ProcessingInfo(document_mode='handwritten', methods=['Gemini Vision (prerecorded)'],
            warnings=fixture['warnings'], unreadable_regions=fixture['unreadable_regions'],
            provenance='Prerecorded synthetic image transcription, not a live Vision result. Professional verification is required for handwritten medicines.')
    else:
        text, method, info = extract_details(path.read_bytes(), path.name)
    result = Analysis.model_validate_json((ROOT / 'demo' / 'expected_outputs' / f'{id}.json').read_text(encoding='utf-8'))
    return text, method, apply_processing_safety(validate_grounding(result, text), info), info
