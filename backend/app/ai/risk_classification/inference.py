def classify_risk(clause_text: str, clause_type: str) -> str:
    """
    Conservative risk logic.
    High risk only when explicitly detected.
    """

    if clause_type == "LIABILITY" and "unlimited" in clause_text.lower():
        return "HIGH"

    if "may" in clause_text.lower():
        return "MEDIUM"

    return "LOW"
