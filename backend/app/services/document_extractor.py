"""Content validation and page-aware printed-document extraction."""
import io
import re
from pathlib import Path
import pymupdf as fitz
from PIL import Image
from fastapi import HTTPException
from ..schemas import ProcessingInfo
from .image_preprocessor import load_image, MAX_PIXELS
from .ocr_service import ocr_available, read_printed

MAX_SIZE = 5 * 1024 * 1024

def validate_file(data, filename):
    if len(data) > MAX_SIZE:
        raise HTTPException(413, 'Choose a file smaller than 5 MB.')
    ext = Path(filename).suffix.lower()
    if ext == '.pdf' and data.startswith(b'%PDF-'):
        return 'application/pdf'
    if ext in ('.png', '.jpg', '.jpeg'):
        load_image(data, ext)
        return 'image/png' if ext == '.png' else 'image/jpeg'
    raise HTTPException(415, 'Upload a genuine PDF, PNG or JPEG document.')

def readable(text):
    chars = [c for c in text if not c.isspace()]
    return (len(chars) >= 20 and len(re.findall(r'\w{2,}', text)) >= 4
            and sum(c.isalnum() for c in chars) / len(chars) > .55
            and '\ufffd' not in text)

def extract_details(data, filename):
    mime = validate_file(data, filename)
    info = ProcessingInfo(provenance='Extracted source text; OCR confidence is not a measure of medical correctness.')
    def scan(image, page_number):
        if not ocr_available():
            raise HTTPException(503, 'OCR is not installed. Install Tesseract or use a text PDF sample.')
        text, steps, warnings = read_printed(image)
        info.methods.append('Tesseract OCR')
        info.preprocessing.extend(steps)
        info.warnings.extend(f'Page {page_number}: {w}' for w in warnings)
        if not readable(text):
            info.warnings.append(f'Page {page_number}: text is sparse or unreadable. Professional clarification is required.')
        return text
    try:
        if mime == 'application/pdf':
            with fitz.open(stream=data, filetype='pdf') as pdf:
                if pdf.needs_pass:
                    raise HTTPException(422, 'Password-protected PDFs are not supported.')
                if not 1 <= len(pdf) <= 10:
                    raise HTTPException(422, 'Use a PDF with 1 to 10 pages.')
                texts = []
                for number, page in enumerate(pdf, 1):
                    text = page.get_text()
                    if readable(text):
                        info.methods.append('PyMuPDF')
                    else:
                        if page.rect.width * page.rect.height * 4 > MAX_PIXELS:
                            raise HTTPException(422, 'PDF page is too large to process safely.')
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                        text = scan(Image.open(io.BytesIO(pix.tobytes('png'))), number)
                    texts.append(text)
                text = '\n'.join(texts)
        else:
            text = scan(load_image(data, Path(filename).suffix.lower()), 1)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(422, 'This document could not be read. Try a clear image or an unprotected PDF.') from None
    if len(text.strip()) < 20:
        raise HTTPException(422, 'No readable text found. Try a clearer document; unreadable details will not be guessed.')
    if len(text) > 40000:
        raise HTTPException(422, 'Document is too long. Upload fewer pages.')
    info.methods = list(dict.fromkeys(info.methods))
    info.preprocessing = list(dict.fromkeys(info.preprocessing))
    method = 'PDF text' if info.methods == ['PyMuPDF'] else 'PDF + Tesseract OCR' if mime == 'application/pdf' else 'Tesseract OCR'
    return text.strip(), method, info

def extract(data, filename):
    text, method, _ = extract_details(data, filename)
    return text, method
