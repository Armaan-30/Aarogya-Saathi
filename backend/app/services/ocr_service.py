import os
import shutil
from pathlib import Path
import pytesseract
from fastapi import HTTPException
from .image_preprocessor import prepare_image

cmd = os.getenv('TESSERACT_CMD') or shutil.which('tesseract')
if not cmd and Path('C:/Program Files/Tesseract-OCR/tesseract.exe').exists():
    cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'
if cmd:
    pytesseract.pytesseract.tesseract_cmd = cmd

def ocr_available():
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False

def read_printed(image):
    if not ocr_available():
        raise HTTPException(503, 'OCR is not installed. Install Tesseract or use a text PDF sample.')
    prepared, steps, warnings = prepare_image(image)
    try:
        try:
            orientation = pytesseract.image_to_osd(prepared, output_type=pytesseract.Output.DICT, timeout=5)
            rotation = int(orientation.get('rotate', 0))
            if rotation and float(orientation.get('orientation_conf', 0)) >= 3:
                prepared = prepared.rotate(-rotation, expand=True)
                steps.append(f'Printed-page orientation corrected by {rotation} degrees')
        except (pytesseract.TesseractError, RuntimeError):
            steps.append('Orientation detection inconclusive; original orientation retained')
        words = pytesseract.image_to_data(prepared, output_type=pytesseract.Output.DICT, timeout=25)
        lines, scores = {}, []
        for index, word in enumerate(words['text']):
            if not word.strip():
                continue
            key = (words['block_num'][index], words['par_num'][index], words['line_num'][index])
            lines.setdefault(key, []).append(word)
            scores.append(float(words['conf'][index]))
        if scores and (sum(scores) / len(scores) < 65 or sum(s < 45 for s in scores) / len(scores) > .15):
            warnings.append('OCR contains low-confidence words. Professional clarification is required before acting on extracted instructions.')
        return '\n'.join(' '.join(words) for words in lines.values()), steps, warnings
    except RuntimeError:
        raise HTTPException(422, 'OCR timed out. Try a smaller, clearer image.') from None
    except pytesseract.TesseractError:
        raise HTTPException(422, 'OCR could not read this image. Try a clearer, upright image.') from None
