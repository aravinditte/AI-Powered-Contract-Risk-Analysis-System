"""
Orchestrator Pipeline

Runs all 3 analysis layers sequentially, cross-validates findings,
and aggregates results into a unified risk report.

Flow:
1. Layer 1: Rule-Based (deterministic, NEVER misses mandatory clauses)
2. Layer 2: NLP/Semantic (ambiguous language, entities, risk classification)
3. Layer 3: RAG (template comparison via vector store, LLM explanations)
4. Template Comparison (clause-by-clause diff)
5. Cross-validation and confidence boosting
6. Unified report generation
"""

import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional

from src.analyzers.rule_based import RuleBasedAnalyzer, Severity
from src.analyzers.nlp_analyzer import NLPAnalyzer
from src.analyzers.rag_analyzer import RAGAnalyzer
from src.analyzers.template_comparator import TemplateComparator

logger = logging.getLogger(__name__)


@dataclass
class Finding:
    id: str
    detecting_layer: str
    clause_type: str
    severity: str
    confidence: float
    clause_text: str
    explanation: str
    suggested_fix: str
    cross_validated: bool = False
    agreeing_layers: list[str] = field(default_factory=list)


@dataclass
class RiskReport:
    contract_id: str
    timestamp: str
    language: str
    overall_risk: str
    overall_score: float
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    findings: list[Finding]
    missing_clauses: list[str]
    entities: Optional[dict]
    template_comparison: Optional[dict]
    layers_used: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


def _split_into_clauses(text: str) -> list[str]:
    """Split contract text into clause-level segments."""
    paragraphs = re.split(r"\n\s*\n", text)
    clauses = []
    for p in paragraphs:
        p = p.strip()
        if len(p) > 30:
            clauses.append(p)
    if not clauses:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        current = ""
        for s in sentences:
            current += " " + s
            if len(current) > 100:
                clauses.append(current.strip())
                current = ""
        if current.strip():
            clauses.append(current.strip())
    return clauses


class AnalysisPipeline:
    """Orchestrates the 3-layer hybrid analysis pipeline."""

    def __init__(self, templates_dir: Optional[str] = None):
        self.rule_analyzer = RuleBasedAnalyzer()
        self.nlp_analyzer = NLPAnalyzer()
        self.rag_analyzer = RAGAnalyzer(templates_dir=templates_dir)
        self.template_comparator = TemplateComparator(templates_dir=templates_dir)

    def analyze(
        self,
        text: str,
        contract_id: str = "",
        language: str = "en",
        template_name: Optional[str] = None,
    ) -> RiskReport:
        """Run the complete 3-layer analysis pipeline."""
        timestamp = datetime.now(timezone.utc).isoformat()
        findings: list[Finding] = []
        finding_counter = 0
        layers_used = []
        entities = None

        # --- Layer 1: Rule-Based (deterministic) ---
        logger.info("Running Layer 1: Rule-Based Analysis")
        try:
            rule_findings = self.rule_analyzer.get_all_findings(text, language)
            layers_used.append("rule_based")
            for rf in rule_findings:
                finding_counter += 1
                findings.append(Finding(
                    id=f"RB-{finding_counter:04d}",
                    detecting_layer="rule_based",
                    clause_type=rf.clause_type,
                    severity=rf.severity.value if isinstance(rf.severity, Severity) else rf.severity,
                    confidence=rf.confidence,
                    clause_text=rf.clause_text,
                    explanation=rf.explanation,
                    suggested_fix=rf.suggested_fix,
                ))
            logger.info(f"Layer 1 produced {len(rule_findings)} findings")
        except Exception as e:
            logger.error(f"Layer 1 failed: {e}")

        # --- Layer 2: NLP/Semantic ---
        logger.info("Running Layer 2: NLP/Semantic Analysis")
        try:
            clauses = _split_into_clauses(text)
            nlp_findings = self.nlp_analyzer.analyze(text, clauses)
            layers_used.append("nlp_semantic")
            for nf in nlp_findings:
                if nf.clause_type == "entities":
                    entities = nf.entities
                    continue
                finding_counter += 1
                findings.append(Finding(
                    id=f"NLP-{finding_counter:04d}",
                    detecting_layer="nlp_semantic",
                    clause_type=nf.clause_type,
                    severity=nf.severity,
                    confidence=nf.confidence,
                    clause_text=nf.clause_text,
                    explanation=nf.explanation,
                    suggested_fix=nf.suggested_fix,
                ))
            logger.info(f"Layer 2 produced {len(nlp_findings)} findings")
        except Exception as e:
            logger.error(f"Layer 2 failed: {e}")

        # --- Layer 3: RAG ---
        logger.info("Running Layer 3: RAG Analysis")
        try:
            rag_findings = self.rag_analyzer.analyze(text, clauses if 'clauses' in dir() else None)
            if rag_findings:
                layers_used.append("rag")
            for ragf in rag_findings:
                finding_counter += 1
                findings.append(Finding(
                    id=f"RAG-{finding_counter:04d}",
                    detecting_layer="rag",
                    clause_type=ragf.clause_type,
                    severity=ragf.severity,
                    confidence=ragf.confidence,
                    clause_text=ragf.clause_text,
                    explanation=ragf.explanation,
                    suggested_fix=ragf.suggested_fix,
                ))
            logger.info(f"Layer 3 produced {len(rag_findings)} findings")
        except Exception as e:
            logger.error(f"Layer 3 failed: {e}")

        # --- Template Comparison ---
        template_result = None
        logger.info("Running Template Comparison")
        try:
            tc_result = self.template_comparator.compare(text, template_name)
            if tc_result:
                layers_used.append("template_comparison")
                template_result = {
                    "overall_similarity": tc_result.overall_similarity,
                    "template_name": tc_result.template_name,
                    "missing_clauses": tc_result.missing_clauses,
                    "modified_clauses": tc_result.modified_clauses,
                    "non_standard_clauses": tc_result.non_standard_clauses,
                    "comparisons_count": len(tc_result.comparisons),
                }
                for comp in tc_result.comparisons:
                    if comp.status != "match":
                        finding_counter += 1
                        findings.append(Finding(
                            id=f"TC-{finding_counter:04d}",
                            detecting_layer="template_comparison",
                            clause_type=comp.clause_type,
                            severity=comp.severity,
                            confidence=comp.similarity_score * 100,
                            clause_text=comp.contract_text or "(missing)",
                            explanation=comp.explanation,
                            suggested_fix=f"Use template language: {comp.template_text[:200]}" if comp.template_text else "",
                        ))
                logger.info(f"Template comparison found {len(tc_result.comparisons)} clause comparisons")
        except Exception as e:
            logger.error(f"Template comparison failed: {e}")

        # --- Cross-validation ---
        findings = self._cross_validate(findings)

        # --- Compute missing clauses ---
        missing_clauses = [
            f.clause_type for f in findings
            if f.detecting_layer == "rule_based"
            and "MISSING" in f.explanation
            and f.severity in ("CRITICAL", "HIGH")
        ]

        # --- Compute overall risk ---
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for f in findings:
            if f.severity in severity_counts:
                severity_counts[f.severity] += 1

        overall_risk, overall_score = self._compute_overall_risk(severity_counts, missing_clauses)

        return RiskReport(
            contract_id=contract_id,
            timestamp=timestamp,
            language=language,
            overall_risk=overall_risk,
            overall_score=overall_score,
            total_findings=len(findings),
            critical_count=severity_counts["CRITICAL"],
            high_count=severity_counts["HIGH"],
            medium_count=severity_counts["MEDIUM"],
            low_count=severity_counts["LOW"],
            info_count=severity_counts["INFO"],
            findings=findings,
            missing_clauses=missing_clauses,
            entities=entities,
            template_comparison=template_result,
            layers_used=layers_used,
        )

    def _cross_validate(self, findings: list[Finding]) -> list[Finding]:
        """Cross-validate findings across layers. If multiple layers agree, boost confidence."""
        clause_groups: dict[str, list[Finding]] = {}
        for f in findings:
            key = f.clause_type.replace("risk_keyword_", "").replace("template_deviation_", "")
            clause_groups.setdefault(key, []).append(f)

        for key, group in clause_groups.items():
            layers = set(f.detecting_layer for f in group)
            if len(layers) > 1:
                for f in group:
                    f.cross_validated = True
                    f.agreeing_layers = list(layers)
                    boost = min(10.0 * (len(layers) - 1), 20.0)
                    f.confidence = min(100.0, f.confidence + boost)

        return findings

    def _compute_overall_risk(
        self, counts: dict[str, int], missing: list[str]
    ) -> tuple[str, float]:
        """Compute overall risk level and score (0-100)."""
        score = 0.0
        score += counts["CRITICAL"] * 25
        score += counts["HIGH"] * 15
        score += counts["MEDIUM"] * 8
        score += counts["LOW"] * 3
        score += len(missing) * 20

        score = min(100.0, score)

        if counts["CRITICAL"] > 0 or len(missing) >= 3:
            return "CRITICAL", score
        elif counts["HIGH"] >= 3 or score >= 60:
            return "HIGH", score
        elif counts["MEDIUM"] >= 3 or score >= 30:
            return "MEDIUM", score
        else:
            return "LOW", score
