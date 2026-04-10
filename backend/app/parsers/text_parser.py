from pathlib import Path


def extract_text_from_txt(file_path: Path) -> str:
    """
    Extract text from plain text contract.
    """

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
