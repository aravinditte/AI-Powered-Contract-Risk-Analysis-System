from app.ai.rules_engine.mandatory_clauses import MANDATORY_CLAUSES


def evaluate_rules(clause_text: str, clause_type: str) -> list:
    """
    Rule-based compliance checks.
    Rules always override ML outputs.
    """

    findings = []

    if clause_type in MANDATORY_CLAUSES and len(clause_text) < 100:
        findings.append("Mandatory clause too short or incomplete.")

    return findings
