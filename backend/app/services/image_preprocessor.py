"""Bounded preparation for printed OCR. Originals are never overwritten."""
import io
import warnings
from PIL import Image, ImageOps, ImageStat
from fastapi import HTTPException

MAX_PIXELS = 20_000_000
Image.MAX_IMAGE_PIXELS = MAX_PIXELS

def load_image(data, extension):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                expected = 'PNG' if extension == '.png' else 'JPEG'
                if image.format != expected:
                    raise HTTPException(415, 'File contents do not match the file type.')
                if image.width * image.height > MAX_PIXELS:
                    raise HTTPException(422, 'Image exceeds the 20 megapixel limit.')
                image.verify()
            with Image.open(io.BytesIO(data)) as image:
                return ImageOps.exif_transpose(image).convert('RGB')
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(422, 'Image could not be read. Upload a genuine, clear PNG or JPEG.') from None

def prepare_image(image):
    steps = ['EXIF orientation applied', 'Grayscale and contrast normalization']
    image = ImageOps.grayscale(image)
    warnings = []
    if ImageStat.Stat(image).stddev[0] < 12:
        warnings.append('Image has very low contrast. Compare every field with the original.')
    image.thumbnail((2600, 2600))
    if max(image.size) < 1200:
        scale = min(2, 1200 / max(image.size))
        image = image.resize((int(image.width * scale), int(image.height * scale)), Image.Resampling.LANCZOS)
        steps.append('Small image resized for OCR')
    image = ImageOps.autocontrast(image)
    return image, steps, warnings
