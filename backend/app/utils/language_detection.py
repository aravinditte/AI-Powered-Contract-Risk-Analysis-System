from langdetect import detect


def detect_language(text: str) -> str:
    """
    Detects contract language.
    Used to route AI models safely.
    """

    try:
        lang = detect(text)
        return lang.upper()
    except Exception:
        return "UNKNOWN"
