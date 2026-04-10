import re

def sanitize_text(text: str) -> str:
    text = re.sub(r"\b\d{12,16}\b", "[REDACTED]", text)
    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\b", "[REDACTED]", text)
    return text
