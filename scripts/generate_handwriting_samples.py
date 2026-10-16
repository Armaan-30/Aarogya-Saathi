"""Create font-rendered synthetic handwriting-lookalikes, not a benchmark."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1] / 'demo'
font = ImageFont.truetype('C:/Windows/Fonts/segoepr.ttf', 38)
label = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 25)
image = Image.new('RGB', (1600, 1150), '#fffef9')
draw = ImageDraw.Draw(image)
draw.text((65, 40), 'SYNTHETIC HACKATHON DEMO - NOT A REAL PRESCRIPTION', font=label, fill='black')
draw.text((65, 82), 'SIMULATED HANDWRITING - FICTIONAL MEDICINES ONLY', font=label, fill='black')
lines = ['Demo Clinic - Sample Patient', '14 October 2026',
         'DemoMed C: [unreadable] tablet once daily.',
         'Duration: [unreadable].', 'Bring this prescription to your next clinic visit.',
         'Follow-up date: [unreadable].']
for n, line in enumerate(lines):
    draw.text((70 + (n % 2)*12, 180 + n*125), line, font=font, fill='#243d60')
image.save(ROOT / 'synthetic_documents/handwritten.png')
blurred = image.copy()
region = blurred.crop((45, 400, 1550, 1030)).filter(ImageFilter.GaussianBlur(8))
blurred.paste(region, (45, 400))
blurred.save(ROOT / 'synthetic_documents/blurry.png')
text = '\n'.join(lines)
items = [
    dict(id='med-1', kind='medicine', title='DemoMed C', wording=lines[2], source=lines[2], frequency='once daily', uncertain=True, concerns=['Dose and duration cannot be read.']),
    dict(id='care-1', kind='instruction', title='Bring the prescription', wording=lines[4], source=lines[4]),
    dict(id='visit-1', kind='follow_up', title='Follow-up needs clarification', wording=lines[5], source=lines[5], uncertain=True, concerns=['Follow-up date cannot be read.']),
]
for name in ('handwritten', 'blurry'):
    # Blurred regions are not magically recovered from their original source.
    transcript = text if name == 'handwritten' else '\n'.join(lines[:2] + ['[unreadable]'])
    fixture = {'text':transcript, 'unreadable_regions':['Medicine dose, duration and follow-up date' if name == 'handwritten' else 'Lower half of prescription'],
               'warnings':['Simulated handwriting contains unreadable fields.' if name == 'handwritten' else 'Heavy blur prevents reliable reading of the prescription.']}
    result = {'document_type':'Synthetic handwritten prescription',
              'summary':'Some prescription details cannot be read. Ask your healthcare professional to clarify them before acting.',
              'items':items if name == 'handwritten' else [], 'uncertainties':fixture['warnings']}
    for suffix, payload in [('-transcription', fixture), ('', result)]:
        (ROOT / 'expected_outputs' / f'{name}{suffix}.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
print('Created two clearly labeled simulated-handwriting images and prerecorded fixtures.')

# Visual-only variants help exercise image upload, preview, scaling and model demos.
# They are typeset fonts, not samples of real handwriting and do not validate accuracy.
variants = {
    'handwriting-script': 'C:/Windows/Fonts/segoesc.ttf',
    'handwriting-comic': 'C:/Windows/Fonts/comici.ttf',
    'handwriting-cursive': 'C:/Windows/Fonts/FRSCRIPT.TTF',
}
for name, font_path in variants.items():
    if not Path(font_path).exists():
        print(f'Skipped {name}: font unavailable ({font_path})')
        continue
    canvas = Image.new('RGB', (1600, 1150), '#fffef9')
    pen = ImageDraw.Draw(canvas)
    pen.text((65, 35), 'SYNTHETIC FONT SAMPLE - NOT A REAL PRESCRIPTION', font=label, fill='black')
    pen.text((65, 75), 'FICTIONAL MEDICINES ONLY - STYLE DEMONSTRATION', font=label, fill='black')
    style_font = ImageFont.truetype(font_path, 49)
    for index, line in enumerate(lines[2:]):
        pen.text((70 + (index % 2) * 20, 190 + index * 145), line, font=style_font, fill='#243d60')
    canvas.save(ROOT / f'synthetic_documents/{name}.png')
    print(f'Created {name}.png using a font-rendered visual style; not human handwriting.')
