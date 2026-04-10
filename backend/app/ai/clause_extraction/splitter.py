import re
from typing import List


def split_into_clauses(text: str) -> List[str]:
    """
    Deterministic clause segmentation.
    Avoids ML to maintain auditability.
    """

    raw_clauses = re.split(r"\n\s*\n|(?<=\.)\s+(?=[A-Z])", text)
    clauses = [c.strip() for c in raw_clauses if len(c.strip()) > 30]

    return clauses
