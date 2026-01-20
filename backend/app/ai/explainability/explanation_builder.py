def build_explanation(
    clause_text: str,
    clause_type: str,
    risk_level: str,
    rule_findings: list,
    deviation: dict,
) -> str:
    reasons = []

    if rule_findings:
        reasons.append("Mandatory rule violation detected.")

    if deviation.get("deviation"):
        reasons.append("Deviation from standard contract template.")

    reasons.append(f"Clause classified as {clause_type}.")
    reasons.append(f"Overall risk assessed as {risk_level}.")

    return " ".join(reasons)
