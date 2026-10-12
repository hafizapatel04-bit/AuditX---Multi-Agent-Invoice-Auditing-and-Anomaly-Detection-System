import os

import pymupdf
import pytesseract
from PIL import Image, ImageOps

from extraction.pdf_text import extract_text, looks_scanned

_WIN_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(_WIN_PATH):
    pytesseract.pytesseract.tesseract_cmd = _WIN_PATH


def _prepare(img: Image.Image) -> Image.Image:
    """Grayscale, upscale small images, boost contrast: helps OCR on low-res scans."""
    img = img.convert("L")
    if img.width < 2000:
        scale = 2000 / img.width
        img = img.resize(
            (int(img.width * scale), int(img.height * scale)),
            Image.Resampling.LANCZOS,
        )
    return ImageOps.autocontrast(img)


def ocr_image(img: Image.Image) -> str:
    return pytesseract.image_to_string(_prepare(img))


def ocr_pdf(file_path: str, dpi: int = 300) -> str:
    """Render each PDF page to an image and run OCR on it."""
    pages = []
    with pymupdf.open(file_path) as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            pages.append(ocr_image(img))
    return "\n".join(pages).strip()


def get_text(file_path: str) -> str:
    """Text PDF -> direct extraction; scanned PDF or image -> OCR."""
    if file_path.lower().endswith(".pdf"):
        return ocr_pdf(file_path) if looks_scanned(file_path) else extract_text(file_path)
    return ocr_image(Image.open(file_path))
