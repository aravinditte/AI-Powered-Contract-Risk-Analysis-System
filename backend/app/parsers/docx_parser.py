from pathlib import Path
import docx


def extract_text_from_docx(file_path: Path) -> str:
    """
    Extract text from DOCX contract.
    """

    document = docx.Document(str(file_path))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]

    return "\n".join(paragraphs)
