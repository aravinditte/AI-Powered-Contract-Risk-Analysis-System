from pathlib import Path
from typing import Optional

from PyPDF2 import PdfReader

from app.parsers.ocr import extract_text_via_ocr


def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extracts text from PDF.
    Falls back to OCR if text is not extractable.
    """

    reader = PdfReader(str(file_path))
    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    full_text = "\n".join(text_parts).strip()

    if not full_text:
        # Scanned PDF fallback
        return extract_text_via_ocr(file_path)

    return full_text
