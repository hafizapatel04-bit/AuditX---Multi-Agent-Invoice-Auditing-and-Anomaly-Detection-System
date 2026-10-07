import os

import pymupdf
import pytesseract
from PIL import Image

from extraction.pdf_text import extract_text, looks_scanned

_WIN_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(_WIN_PATH):
    pytesseract.pytesseract.tesseract_cmd = _WIN_PATH


def ocr_pdf(file_path: str, dpi: int = 300) -> str:
    """Render each PDF page to an image and run OCR on it."""
    pages = []
    with pymupdf.open(file_path) as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            pages.append(pytesseract.image_to_string(img))
    return "\n".join(pages).strip()


def get_text(file_path: str) -> str:
    """Single entry point: text PDF -> direct extraction, scanned PDF or image -> OCR."""
    if file_path.lower().endswith(".pdf"):
        return ocr_pdf(file_path) if looks_scanned(file_path) else extract_text(file_path)
    return pytesseract.image_to_string(Image.open(file_path))
