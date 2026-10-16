"""Quick, repeatable OCR smoke evaluation over fictional synthetic print.

Run with backend/.venv/Scripts/python scripts/evaluate_synthetic_ocr.py.
This is a calibration aid, not evidence of medical or handwriting accuracy.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.ocr_service import read_printed  # noqa: E402

FONT = Path("C:/Windows/Fonts/arial.ttf")
EXPECTED = [
    "SYNTHETIC DOCUMENT ONLY",
    "DemoMed A 1 tablet once daily for 3 days",
    "Keep the dressing clean and dry",
    "Follow up at the sample clinic on 22 October",
]


def normalize(value):
    return " ".join("".join(c.lower() for c in value if c.isalnum() or c.isspace()).split())


def word_error_rate(expected, actual):
    ref, hyp = normalize(expected).split(), normalize(actual).split()
    row = list(range(len(hyp) + 1))
    for i, word in enumerate(ref, 1):
        nxt = [i]
        for j, found in enumerate(hyp, 1):
            nxt.append(min(nxt[-1] + 1, row[j] + 1, row[j - 1] + (word != found)))
        row = nxt
    return row[-1] / max(len(ref), 1)


def make_image(size, color, blur=0, angle=0):
    image = Image.new("RGB", (1500, 520), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(FONT), size)
    for index, line in enumerate(EXPECTED):
        draw.text((55, 35 + index * 112), line, font=font, fill=color)
    if blur:
        image = image.filter(ImageFilter.GaussianBlur(blur))
    if angle:
        image = image.rotate(angle, expand=True, fillcolor="white")
    return image


def main():
    if not FONT.exists():
        raise SystemExit(f"Install a sans-serif test font or update FONT: {FONT}")
    cases = [
        ("clear print", make_image(38, "#101820")),
        ("small print", make_image(22, "#101820")),
        ("faint print", make_image(34, "#b8b8b8")),
        ("slight blur and rotation", make_image(32, "#182538", blur=0.7, angle=2)),
    ]
    for name, image in cases:
        actual, _, warnings = read_printed(image)
        wer = word_error_rate(" ".join(EXPECTED), actual)
        print(f"{name}: WER={wer:.0%}; quality_warning={bool(warnings)}")
        if wer:
            print(f"  OCR: {actual[:220].replace(chr(10), ' | ')}")


if __name__ == "__main__":
    main()
