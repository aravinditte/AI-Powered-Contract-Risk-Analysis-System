def check_template_deviation(clause_text: str, clause_type: str) -> dict:
    """
    Placeholder semantic comparison.
    Deterministic threshold-based output.
    """

    # TODO: integrate sentence-transformers
    similarity_score = 0.65

    if similarity_score < 0.70:
        return {
            "deviation": True,
            "score": similarity_score,
            "standard_clause": "Company-approved standard clause text",
        }

    return {
        "deviation": False,
        "score": similarity_score,
        "standard_clause": None,
    }
