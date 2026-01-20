def classify_clause(clause_text: str) -> str:
    """
    Placeholder inference.
    Replace with fine-tuned model.
    """

    text = clause_text.lower()

    if "terminate" in text:
        return "TERMINATION"
    if "confidential" in text:
        return "NDA"
    if "payment" in text or "fee" in text:
        return "PAYMENT"

    return "OTHER"
