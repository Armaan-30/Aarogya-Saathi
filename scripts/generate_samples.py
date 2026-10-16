"""Generate fictional fixtures, text PDFs and a real raster OCR sample."""
import json
from pathlib import Path
import fitz
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'demo'
BANNER = 'SYNTHETIC HACKATHON DEMO - NOT A REAL PRESCRIPTION'

def item(id, kind, title, source, **extra):
    return dict(id=id, kind=kind, title=title, wording=source, source=source, **extra)

clear = [
    item('med-1', 'medicine', 'DemoMed A', 'DemoMed A: 1 tablet once daily at 08:00 after breakfast for 3 days.', dosage='1 tablet', frequency='once daily', duration='for 3 days', timing='08:00'),
    item('care-1', 'instruction', 'Keep the dressing dry', 'Keep the dressing clean and dry.'),
    item('care-2', 'instruction', 'Rest at home', 'Rest at home for 2 days. Avoid heavy lifting for 7 days.'),
    item('visit-1', 'follow_up', 'Follow-up appointment', 'Return to the outpatient clinic on 22 October 2026 at 10:00. Bring this summary.', date='22 October 2026', timing='10:00'),
    item('warn-1', 'warning', 'When to contact the clinic', 'Contact the clinic if the dressing becomes soaked or redness increases.'),
]
incomplete = [
    item('med-1', 'medicine', 'DemoMed B', 'DemoMed B: twice daily. Dose and duration unclear.', frequency='twice daily', uncertain=True, concerns=['Dose and duration are missing. Ask the prescribing professional.']),
    item('care-1', 'instruction', 'Bring the prescription', 'Bring this prescription to your next clinic visit.'),
    item('visit-1', 'follow_up', 'Follow-up needs clarification', 'Follow-up date: unclear.', uncertain=True, concerns=['Follow-up date is not readable.']),
]
cases = [
    ('clear', 'Clear discharge summary', clear, 'Your document describes dressing care, rest, a fictional medicine and a clinic follow-up. Review each instruction against the original before creating your checklist.'),
    ('incomplete', 'Incomplete prescription', incomplete, 'Some prescription details are missing. Ask your healthcare professional to clarify the medicine dose, duration and follow-up date.'),
    ('scanned', 'Scanned discharge summary', clear, 'This scanned sample describes dressing care, rest, a fictional medicine and a clinic follow-up. Check OCR wording carefully against the original.'),
]
for id, title, items, summary in cases:
    text = '\n'.join([BANNER, 'AAROGYASAATHI DEMONSTRATION CLINIC', title.upper(), 'Fictional patient: Sample Patient', 'Document date: 14 October 2026', 'Fictional medication names for demonstration only.', '', *[i['source'] for i in items]])
    (OUT / 'synthetic_documents' / f'{id}.txt').write_text(text, encoding='utf-8')
    result = {'document_type':title, 'summary':summary, 'items':items, 'uncertainties': ['Missing medicine details and follow-up date require professional clarification.'] if id == 'incomplete' else []}
    (OUT / 'expected_outputs' / f'{id}.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    if id == 'scanned':
        img = Image.new('RGB', (1800, 1300), 'white')
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 27)
        for n, line in enumerate(text.splitlines()): draw.text((65, 70+n*70), line, fill='black', font=font)
        img.save(OUT / 'synthetic_documents' / 'scanned.png')
        img.save(OUT / 'synthetic_documents' / 'scanned.jpg')
        pdf = fitz.open(); page = pdf.new_page(width=900, height=650)
        page.insert_image(page.rect, filename=str(OUT / 'synthetic_documents' / 'scanned.png'))
        pdf.save(OUT / 'synthetic_documents' / 'scanned.pdf', deflate=True); pdf.close()
    else:
        pdf = fitz.open(); page = pdf.new_page()
        page.insert_textbox(fitz.Rect(42, 45, 553, 790), text, fontsize=12, lineheight=1.6)
        pdf.save(OUT / 'synthetic_documents' / f'{id}.pdf'); pdf.close()
print('Generated 3 synthetic cases, 4 PDFs/images and expected JSON fixtures.')
