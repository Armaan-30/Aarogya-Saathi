"""Check access without printing credentials or raw provider errors."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.services.gemini_service import client, analyze
from app.config import ROOT, MODEL
from google.genai import errors
from fastapi import HTTPException

try:
    with client() as sdk:
        model = sdk.models.get(model=MODEL)
        print('Configured model is accessible:', model.name)
    text = (ROOT / 'demo/synthetic_documents/clear.txt').read_text(encoding='utf-8')
    result = analyze(text)
    print('Live structured analysis succeeded:', len(result.items), 'items;', sum(i.uncertain for i in result.items), 'requiring clarification')
except errors.APIError as exc:
    print('Gemini access check failed. HTTP status:', exc.code)
    print('No alternate model or paid service was used.')
    sys.exit(1)
except HTTPException as exc:
    print('Gemini check:', exc.detail)
    sys.exit(1)
except Exception:
    print('Gemini check failed due to a network or SDK error. Credentials were not logged.')
    sys.exit(1)
