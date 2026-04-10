"""
Template Comparison Engine

Compares uploaded contracts against company-approved templates.
- Clause-by-clause diff with similarity scores
- Detects missing, modified, and non-standard clauses
- Uses sentence-transformers for semantic similarity
- Falls back to text-based comparison if models unavailable
"""

import logging
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ClauseComparison:
    clause_type: str
    contract_text: str
    template_text: str
    similarity_score: float
    status: str  # "match", "modified", "missing_in_contract", "non_standard"
    severity: str
    explanation: str
    detecting_layer: str = "template_comparison"


@dataclass
class TemplateComparisonResult:
    overall_similarity: float
    comparisons: list[ClauseComparison]
    missing_clauses: list[str]
    modified_clauses: list[str]
    non_standard_clauses: list[str]
    template_name: str


CLAUSE_SECTION_PATTERNS = [
    r"(?m)^(\d+[\.\)]\s+[A-Z][^\n]+)",
    r"(?m)^(ARTICLE\s+\w+[:\.\s]+[^\n]+)",
    r"(?m)^(Section\s+\d+[:\.\s]+[^\n]+)",
    r"(?m)^(CLAUSE\s+\d+[:\.\s]+[^\n]+)",
    r"(?m)^([A-Z][A-Z\s]{3,}:)",
    r"(?m)^(第\d+条[^\n]*)",
]


class TemplateComparator:
    """Compare contracts against approved templates clause-by-clause."""

    def __init__(self, templates_dir: Optional[str] = None):
        self.templates_dir = templates_dir or str(
            Path(__file__).parent.parent.parent / "data" / "templates"
        )
        self.templates: dict[str, dict] = {}
        self._nlp_analyzer = None

    def load_templates(self):
        """Load all template files from the templates directory."""
        templates_path = Path(self.templates_dir)
        if not templates_path.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return

        for template_file in templates_path.glob("*.txt"):
            content = template_file.read_text(encoding="utf-8")
            clauses = self._extract_clauses(content)
            self.templates[template_file.stem] = {
                "name": template_file.stem,
                "full_text": content,
                "clauses": clauses,
                "path": str(template_file),
            }
            logger.info(f"Loaded template: {template_file.stem} ({len(clauses)} clauses)")

    def compare(
        self,
        contract_text: str,
        template_name: Optional[str] = None,
    ) -> Optional[TemplateComparisonResult]:
        """Compare a contract against a template."""
        if not self.templates:
            self.load_templates()

        if not self.templates:
            logger.warning("No templates available for comparison")
            return None

        if template_name and template_name in self.templates:
            template = self.templates[template_name]
        else:
            template = self._find_best_template(contract_text)

        if template is None:
            return None

        contract_clauses = self._extract_clauses(contract_text)
        template_clauses = template["clauses"]

        comparisons = []
        missing_clauses = []
        modified_clauses = []
        non_standard_clauses = []
        total_similarity = 0.0
        comparison_count = 0

        for t_type, t_data in template_clauses.items():
            best_match = self._find_best_clause_match(t_data["text"], contract_clauses)

            if best_match is None or best_match["score"] < 0.2:
                missing_clauses.append(t_type)
                comparisons.append(ClauseComparison(
                    clause_type=t_type,
                    contract_text="",
                    template_text=t_data["text"][:300],
                    similarity_score=0.0,
                    status="missing_in_contract",
                    severity="HIGH" if t_type in self._critical_types() else "MEDIUM",
                    explanation=f"Clause '{t_type}' from template is missing in the contract.",
                ))
            else:
                score = best_match["score"]
                total_similarity += score
                comparison_count += 1

                if score >= 0.85:
                    status = "match"
                    severity = "INFO"
                    explanation = f"Clause closely matches template (similarity: {score:.1%})."
                elif score >= 0.6:
                    status = "modified"
                    severity = "MEDIUM"
                    explanation = f"Clause has been modified from template (similarity: {score:.1%}). Review changes."
                    modified_clauses.append(t_type)
                else:
                    status = "modified"
                    severity = "HIGH"
                    explanation = f"Clause significantly deviates from template (similarity: {score:.1%}). Careful review needed."
                    modified_clauses.append(t_type)

                comparisons.append(ClauseComparison(
                    clause_type=t_type,
                    contract_text=best_match["text"][:300],
                    template_text=t_data["text"][:300],
                    similarity_score=score,
                    status=status,
                    severity=severity,
                    explanation=explanation,
                ))

        for c_type, c_data in contract_clauses.items():
            if not self._has_template_match(c_data["text"], template_clauses):
                non_standard_clauses.append(c_type)
                comparisons.append(ClauseComparison(
                    clause_type=c_type,
                    contract_text=c_data["text"][:300],
                    template_text="",
                    similarity_score=0.0,
                    status="non_standard",
                    severity="MEDIUM",
                    explanation=f"Non-standard clause '{c_type}' not found in approved template.",
                ))

        overall_similarity = (total_similarity / comparison_count * 100) if comparison_count > 0 else 0.0

        return TemplateComparisonResult(
            overall_similarity=round(overall_similarity, 1),
            comparisons=comparisons,
            missing_clauses=missing_clauses,
            modified_clauses=modified_clauses,
            non_standard_clauses=non_standard_clauses,
            template_name=template["name"],
        )

    def _extract_clauses(self, text: str) -> dict[str, dict]:
        """Extract and categorize clauses from text."""
        clauses = {}
        for pattern in CLAUSE_SECTION_PATTERNS:
            matches = list(re.finditer(pattern, text))
            if matches:
                for i, match in enumerate(matches):
                    start = match.start()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                    heading = match.group(1).strip()
                    body = text[start:end].strip()
                    clause_type = self._classify_heading(heading)
                    if len(body) > 20:
                        clauses[clause_type] = {"heading": heading, "text": body}
                break

        if not clauses:
            paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
            for i, para in enumerate(paragraphs):
                clause_type = f"section_{i + 1}"
                clauses[clause_type] = {"heading": f"Section {i + 1}", "text": para}

        return clauses

    def _classify_heading(self, heading: str) -> str:
        """Classify a section heading into a clause type."""
        heading_lower = heading.lower()
        mappings = {
            "govern": "governing_law", "jurisdict": "governing_law", "applicable law": "governing_law",
            "terminat": "termination", "cancel": "termination", "exit": "termination",
            "payment": "payment_terms", "fee": "payment_terms", "compensat": "payment_terms", "invoic": "payment_terms",
            "confidential": "confidentiality", "non-disclosure": "confidentiality", "nda": "confidentiality",
            "intellectual property": "ip_ownership", "ip ": "ip_ownership", "copyright": "ip_ownership",
            "liabilit": "liability", "indemnif": "liability", "limitation of": "liability",
            "force majeure": "force_majeure",
            "dispute": "dispute_resolution", "arbitrat": "dispute_resolution", "mediat": "dispute_resolution",
            "data protect": "data_protection", "privacy": "data_protection", "personal data": "data_protection",
            "non-compet": "non_compete", "non-solicitat": "non_compete", "restrictive": "non_compete",
            "scope of": "working_hours", "deliverable": "working_hours", "working hour": "working_hours",
            "tax": "tax_obligations", "withhold": "tax_obligations",
            "insurance": "insurance",
            "amendment": "amendments", "modif": "amendments",
            "notice": "notice", "notification": "notice",
            "severab": "severability",
            "entire agreement": "entire_agreement", "whole agreement": "entire_agreement",
            "assign": "assignment", "delegat": "assignment",
            "warrant": "warranties", "represent": "warranties",
            "renew": "auto_renewal", "term and": "auto_renewal",
        }
        for keyword, clause_type in mappings.items():
            if keyword in heading_lower:
                return clause_type
        return re.sub(r"[^\w]+", "_", heading_lower).strip("_")[:50]

    def _find_best_clause_match(self, template_text: str, contract_clauses: dict) -> Optional[dict]:
        """Find the best matching clause in the contract for a template clause."""
        best_score = 0.0
        best_text = ""

        for c_type, c_data in contract_clauses.items():
            score = self._compute_similarity(template_text, c_data["text"])
            if score > best_score:
                best_score = score
                best_text = c_data["text"]

        if best_score > 0.0:
            return {"score": best_score, "text": best_text}
        return None

    def _has_template_match(self, contract_text: str, template_clauses: dict) -> bool:
        """Check if a contract clause has a reasonable match in the template."""
        for t_type, t_data in template_clauses.items():
            score = self._compute_similarity(contract_text, t_data["text"])
            if score >= 0.4:
                return True
        return False

    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Compute similarity between two texts."""
        try:
            from src.analyzers.nlp_analyzer import NLPAnalyzer
            analyzer = NLPAnalyzer()
            score = analyzer.compute_similarity(text1[:500], text2[:500])
            if score is not None:
                return score
        except Exception:
            pass
        return SequenceMatcher(None, text1.lower()[:500], text2.lower()[:500]).ratio()

    def _find_best_template(self, contract_text: str) -> Optional[dict]:
        """Find the most relevant template for a contract."""
        if not self.templates:
            return None
        if len(self.templates) == 1:
            return next(iter(self.templates.values()))

        best_score = 0.0
        best_template = None
        for name, template in self.templates.items():
            score = SequenceMatcher(
                None,
                contract_text.lower()[:1000],
                template["full_text"].lower()[:1000],
            ).ratio()
            if score > best_score:
                best_score = score
                best_template = template

        return best_template

    @staticmethod
    def _critical_types() -> set[str]:
        """Clause types that are critical if missing."""
        return {
            "governing_law", "termination", "payment_terms",
            "liability", "confidentiality", "ip_ownership",
        }
