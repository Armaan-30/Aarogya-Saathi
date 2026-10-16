"""Text understanding stays separate from image transcription."""
from fastapi import HTTPException
from ..schemas import Analysis
from .gemini_service import generate, SYSTEM
from .safety import validate_grounding

def analyze(text):
    result = generate('DOCUMENT DATA:\n' + text, Analysis, SYSTEM)
    try:
        return validate_grounding(result, text)
    except ValueError:
        raise HTTPException(502, 'AI response failed validation. Please retry.') from None
