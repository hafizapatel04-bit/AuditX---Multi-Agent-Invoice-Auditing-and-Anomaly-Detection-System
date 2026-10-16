import os

import pymupdf
import pytesseract
from PIL import Image, ImageFilter, ImageOps

_WIN_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(_WIN_PATH):
    pytesseract.pytesseract.tesseract_cmd = _WIN_PATH

# --- tuning knobs (set these from the OCR experiment) ---
DPI = 300          # render resolution for PDF pages
PSM = 4            # Tesseract page segmentation mode
MIN_WIDTH = 2000   # upscale smaller images to at least this width
SHARPEN = False
DENOISE = False    # median filter to remove speckle noise
THRESHOLD = None   # e.g. 140 for black/white; None = keep grayscale
MAX_PAGES = 5      # invoices are short; skip the rest
MIN_CHARS = 50     # a PDF page with less text than this is treated as scanned


def _prepare(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    if img.width < MIN_WIDTH:
        scale = MIN_WIDTH / img.width
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
    img = ImageOps.autocontrast(img)
    if DENOISE:
        img = img.filter(ImageFilter.MedianFilter(3))
    if SHARPEN:
        img = img.filter(ImageFilter.SHARPEN)
    if THRESHOLD:
        img = img.point(lambda p: 255 if p > THRESHOLD else 0)
    return img


def ocr_image(img: Image.Image) -> str:
    return pytesseract.image_to_string(_prepare(img), config=f"--psm {PSM}")


def _ocr_page(page) -> str:
    pix = page.get_pixmap(dpi=DPI)
    return ocr_image(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))


def ocr_pdf(file_path: str) -> str:
    """Force OCR on every page (used for testing)."""
    with pymupdf.open(file_path) as doc:
        return "\n".join(_ocr_page(p) for i, p in enumerate(doc) if i < MAX_PAGES).strip()


def get_text(file_path: str) -> str:
    """Real text where the PDF has it, OCR only for pages that are scans. Images are always OCR'd."""
    if not file_path.lower().endswith(".pdf"):
        return ocr_image(Image.open(file_path)).strip()
    pages = []
    with pymupdf.open(file_path) as doc:
        for i, page in enumerate(doc):
            if i >= MAX_PAGES:
                break
            text = page.get_text().strip()
            pages.append(text if len(text) >= MIN_CHARS else _ocr_page(page))
    return "\n".join(pages).strip()
