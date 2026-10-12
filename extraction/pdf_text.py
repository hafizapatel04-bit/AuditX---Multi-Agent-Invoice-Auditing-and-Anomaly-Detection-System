import pymupdf


def extract_text(file_path: str) -> str:
    pages = []
    with pymupdf.open(file_path) as doc:
        for page in doc:
            pages.append(page.get_text())
    return "\n".join(pages).strip()


def looks_scanned(file_path: str, min_chars: int = 50) -> bool:
    """If almost no text came out, the PDF is probably a scanned image (needs OCR)."""
    return len(extract_text(file_path)) < min_chars