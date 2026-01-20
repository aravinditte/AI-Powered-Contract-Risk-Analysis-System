from pathlib import Path
import pytesseract
from PIL import Image
from pdf2image import convert_from_path


def extract_text_via_ocr(file_path: Path) -> str:
    """
    OCR extraction for scanned PDFs.
    Explicitly separated for compliance review.
    """

    images = convert_from_path(str(file_path))
    extracted_text = []

    for image in images:
        text = pytesseract.image_to_string(image, lang="eng")
        extracted_text.append(text)

    return "\n".join(extracted_text)
