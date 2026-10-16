from fastapi import HTTPException
from google.genai import errors

from .gemini_service import client, require_live

MODEL = 'gemini-3.8-flash-lite-tts'


def synthesize(text: str, language: str) -> dict:
    if language not in {'hi', 'mr'}:
        raise HTTPException(422, 'Speech generation supports Hindi and Marathi.')
    if not text.strip() or len(text) > 5000:
        raise HTTPException(422, 'The explanation is empty or too long to read aloud.')
    require_live()
    try:
        with client() as sdk:
            result = sdk.interactions.create(
                model=MODEL,
                input=[{
                    'type': 'user_input',
                    'content': [{
                        'type': 'text',
                        'text': text,
                        'annotations': [{
                            'type': 'speech_metadata',
                            'style': 'Speak clearly and calmly at a measured pace. Read the supplied text verbatim.',
                        }],
                    }],
                }],
                response_format={'type': 'audio'},
                generation_config={'speech_config': [{'voice': 'Kore'}]},
            )
        audio = result.output_audio
        if not audio or not audio.data or audio.mime_type != 'audio/wav':
            raise HTTPException(502, 'Speech service returned no playable audio.')
        return {'language': language, 'mime_type': 'audio/wav', 'audio_base64': audio.data}
    except HTTPException:
        raise
    except errors.APIError as exc:
        if exc.code == 429:
            raise HTTPException(503, 'Free-tier speech quota is unavailable. Try again later or use the readable text.') from None
        if exc.code in (400, 404):
            raise HTTPException(503, 'The configured free-tier speech model is unavailable for this project.') from None
        raise HTTPException(503, 'Speech generation is temporarily unavailable. The explanation remains readable.') from None
    except Exception:
        raise HTTPException(502, 'Speech generation failed. The explanation remains readable.') from None
