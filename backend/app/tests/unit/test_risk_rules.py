from app.ai.rules_engine.rule_evaluator import evaluate_rules


def test_mandatory_clause_too_short():
    clause_text = "Payment shall be made."
    clause_type = "PAYMENT"

    findings = evaluate_rules(clause_text, clause_type)

    assert len(findings) == 1
    assert "Mandatory clause" in findings[0]


def test_non_mandatory_clause_no_findings():
    clause_text = "General terms apply."
    clause_type = "OTHER"

    findings = evaluate_rules(clause_text, clause_type)

    assert findings == []
