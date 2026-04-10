from typing import List

from app.ai.clause_extraction.splitter import split_into_clauses
from app.ai.clause_classification.inference import classify_clause
from app.ai.risk_classification.inference import classify_risk
from app.ai.template_analysis.similarity import check_template_deviation
from app.ai.rules_engine.rule_evaluator import evaluate_rules
from app.ai.explainability.explanation_builder import build_explanation
from app.ai.explainability.confidence_calculator import calculate_confidence


def run_ai_pipeline(contract_text: str, language: str = "EN") -> List[dict]:
    """
    AI decision-support pipeline.
    Returns explainable risk findings.
    """

    results = []
    clauses = split_into_clauses(contract_text)

    for clause_text in clauses:
        clause_type = classify_clause(clause_text)
        rule_findings = evaluate_rules(clause_text, clause_type)

        risk_level = classify_risk(clause_text, clause_type)
        deviation = check_template_deviation(clause_text, clause_type)

        explanation = build_explanation(
            clause_text=clause_text,
            clause_type=clause_type,
            risk_level=risk_level,
            rule_findings=rule_findings,
            deviation=deviation,
        )

        confidence = calculate_confidence(
            rule_findings=rule_findings,
            deviation=deviation,
        )

        results.append({
            "clause_text": clause_text,
            "clause_type": clause_type,
            "risk_level": risk_level,
            "explanation": explanation,
            "confidence": confidence,
            "compared_standard_clause": deviation.get("standard_clause"),
        })

    return results
