def calculate_confidence(rule_findings: list, deviation: dict) -> float:
    """
    Conservative confidence estimation.
    """

    confidence = 0.5

    if rule_findings:
        confidence += 0.2

    if deviation.get("deviation"):
        confidence += 0.2

    return min(confidence, 0.95)
