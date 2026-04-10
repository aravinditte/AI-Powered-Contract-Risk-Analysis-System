"""
Layer 2: NLP/Semantic Analysis Engine

Uses local free models only (ZERO API cost):
- sentence-transformers (all-MiniLM-L6-v2) for semantic embeddings
- spaCy for Named Entity Recognition
- HuggingFace zero-shot classification for risk levels
- Detects ambiguous language, vague terms, one-sided provisions

Graceful fallback: if models aren't available, returns empty results
rather than crashing.
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy-loaded model holders
_sentence_model = None
_nlp_model = None
_zero_shot_classifier = None


@dataclass
class NLPFinding:
    clause_type: str
    severity: str
    confidence: float
    clause_text: str
    explanation: str
    suggested_fix: str
    detecting_layer: str = "nlp_semantic"
    entities: Optional[dict] = None


AMBIGUOUS_PATTERNS = [
    (r"(?i)\b(reasonable|reasonably)\b", "Vague term 'reasonable' — subjective interpretation risk."),
    (r"(?i)\b(best\s+efforts?|commercially\s+reasonable)\b", "Vague obligation standard — may be difficult to enforce."),
    (r"(?i)\b(may\s+change|subject\s+to\s+change)\b", "Unilateral modification risk — terms can change without consent."),
    (r"(?i)\b(at\s+any\s+time|from\s+time\s+to\s+time)\b", "Open-ended timing — no fixed schedule or deadline."),
    (r"(?i)\b(including\s+but\s+not\s+limited\s+to)\b", "Open-ended list — scope is intentionally undefined."),
    (r"(?i)\b(as\s+deemed\s+necessary|as\s+appropriate)\b", "Subjective standard — relies on one party's judgment."),
    (r"(?i)\b(material(ly)?)\s+(adverse|breach|change)\b", "Materiality threshold is subjective without quantification."),
    (r"(?i)\b(promptly|timely|without\s+delay)\b", "Vague time requirement — no specific deadline."),
]

ONE_SIDED_PATTERNS = [
    (r"(?i)\bshall\s+not\s+be\s+(liable|responsible)\b", "One-sided liability exclusion detected."),
    (r"(?i)\b(sole\s+and\s+exclusive|only)\s+remed(y|ies)\b", "Remedy limitations favor one party."),
    (r"(?i)\bwithout\s+(any\s+)?(liability|obligation|cost)\b", "Cost/liability exclusion is one-sided."),
    (r"(?i)\b(irrevocably|unconditionally)\s+(waive|consent|agree)\b", "Irrevocable waiver — cannot be reversed."),
    (r"(?i)\breserves?\s+the\s+right\b", "Reserved rights may create imbalanced obligations."),
]

RISK_LABELS = [
    "high risk clause",
    "medium risk clause",
    "low risk clause",
    "standard clause",
    "favorable clause",
]


def _load_sentence_model():
    """Lazy load sentence-transformers model."""
    global _sentence_model
    if _sentence_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Loaded sentence-transformers model: all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"Could not load sentence-transformers: {e}")
            _sentence_model = False
    return _sentence_model if _sentence_model is not False else None


def _load_spacy():
    """Lazy load spaCy model."""
    global _nlp_model
    if _nlp_model is None:
        try:
            import spacy
            try:
                _nlp_model = spacy.load("en_core_web_sm")
            except OSError:
                logger.info("Downloading spaCy en_core_web_sm model...")
                from spacy.cli import download
                download("en_core_web_sm")
                _nlp_model = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model: en_core_web_sm")
        except Exception as e:
            logger.warning(f"Could not load spaCy: {e}")
            _nlp_model = False
    return _nlp_model if _nlp_model is not False else None


def _load_zero_shot():
    """Lazy load zero-shot classification pipeline."""
    global _zero_shot_classifier
    if _zero_shot_classifier is None:
        try:
            from transformers import pipeline
            _zero_shot_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=-1,
            )
            logger.info("Loaded zero-shot classifier: facebook/bart-large-mnli")
        except Exception as e:
            logger.warning(f"Could not load zero-shot classifier: {e}")
            _zero_shot_classifier = False
    return _zero_shot_classifier if _zero_shot_classifier is not False else None


class NLPAnalyzer:
    """Layer 2: NLP/Semantic analysis using free local models."""

    def __init__(self):
        self.ambiguous_patterns = AMBIGUOUS_PATTERNS
        self.one_sided_patterns = ONE_SIDED_PATTERNS

    def analyze(self, text: str, clauses: Optional[list[str]] = None) -> list[NLPFinding]:
        """Run complete NLP analysis on contract text."""
        findings = []

        findings.extend(self._detect_ambiguous_language(text))
        findings.extend(self._detect_one_sided_provisions(text))

        entities = self._extract_entities(text)
        if entities:
            findings.append(NLPFinding(
                clause_type="entities",
                severity="INFO",
                confidence=80.0,
                clause_text="",
                explanation=f"Extracted entities: {self._format_entities(entities)}",
                suggested_fix="",
                entities=entities,
            ))

        if clauses:
            findings.extend(self._classify_clause_risks(clauses))

        return findings

    def get_embeddings(self, texts: list[str]):
        """Get sentence embeddings for texts. Returns None if model unavailable."""
        model = _load_sentence_model()
        if model is None:
            return None
        try:
            return model.encode(texts, show_progress_bar=False)
        except Exception as e:
            logger.warning(f"Embedding failed: {e}")
            return None

    def compute_similarity(self, text1: str, text2: str) -> Optional[float]:
        """Compute cosine similarity between two texts."""
        model = _load_sentence_model()
        if model is None:
            return None
        try:
            from sentence_transformers import util
            emb1 = model.encode(text1, convert_to_tensor=True)
            emb2 = model.encode(text2, convert_to_tensor=True)
            similarity = util.cos_sim(emb1, emb2).item()
            return float(similarity)
        except Exception as e:
            logger.warning(f"Similarity computation failed: {e}")
            return None

    def _detect_ambiguous_language(self, text: str) -> list[NLPFinding]:
        """Detect ambiguous or vague language patterns."""
        findings = []
        for pattern, description in self.ambiguous_patterns:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                start = max(0, match.start() - 80)
                end = min(len(text), match.end() + 80)
                context = text[start:end].strip()
                findings.append(NLPFinding(
                    clause_type="ambiguous_language",
                    severity="MEDIUM",
                    confidence=75.0,
                    clause_text=context,
                    explanation=description,
                    suggested_fix="Replace vague language with specific, quantifiable terms.",
                ))
        return findings

    def _detect_one_sided_provisions(self, text: str) -> list[NLPFinding]:
        """Detect one-sided or imbalanced provisions."""
        findings = []
        for pattern, description in self.one_sided_patterns:
            matches = list(re.finditer(pattern, text))
            for match in matches:
                start = max(0, match.start() - 80)
                end = min(len(text), match.end() + 80)
                context = text[start:end].strip()
                findings.append(NLPFinding(
                    clause_type="one_sided_provision",
                    severity="HIGH",
                    confidence=70.0,
                    clause_text=context,
                    explanation=description,
                    suggested_fix="Negotiate balanced terms that protect both parties equally.",
                ))
        return findings

    def _extract_entities(self, text: str) -> Optional[dict]:
        """Extract named entities using spaCy."""
        nlp = _load_spacy()
        if nlp is None:
            return None

        try:
            doc = nlp(text[:100000])  # spaCy can be slow on very long texts
            entities = {
                "organizations": [],
                "persons": [],
                "dates": [],
                "money": [],
                "locations": [],
            }
            seen = set()
            for ent in doc.ents:
                key = (ent.label_, ent.text.strip())
                if key in seen:
                    continue
                seen.add(key)
                if ent.label_ == "ORG":
                    entities["organizations"].append(ent.text.strip())
                elif ent.label_ == "PERSON":
                    entities["persons"].append(ent.text.strip())
                elif ent.label_ == "DATE":
                    entities["dates"].append(ent.text.strip())
                elif ent.label_ == "MONEY":
                    entities["money"].append(ent.text.strip())
                elif ent.label_ in ("GPE", "LOC"):
                    entities["locations"].append(ent.text.strip())
            return entities
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
            return None

    def _classify_clause_risks(self, clauses: list[str]) -> list[NLPFinding]:
        """Classify risk level of individual clauses using zero-shot classification."""
        classifier = _load_zero_shot()
        if classifier is None:
            return []

        findings = []
        try:
            for clause in clauses:
                if len(clause.strip()) < 20:
                    continue
                truncated = clause[:512]
                result = classifier(truncated, RISK_LABELS, multi_label=False)
                top_label = result["labels"][0]
                top_score = result["scores"][0]

                if "high risk" in top_label and top_score > 0.4:
                    findings.append(NLPFinding(
                        clause_type="nlp_risk_classification",
                        severity="HIGH",
                        confidence=round(top_score * 100, 1),
                        clause_text=truncated[:200],
                        explanation=f"Zero-shot classifier identified this as a high risk clause (confidence: {top_score:.1%}).",
                        suggested_fix="Review this clause carefully for unfavorable terms.",
                    ))
                elif "medium risk" in top_label and top_score > 0.4:
                    findings.append(NLPFinding(
                        clause_type="nlp_risk_classification",
                        severity="MEDIUM",
                        confidence=round(top_score * 100, 1),
                        clause_text=truncated[:200],
                        explanation=f"Zero-shot classifier identified this as a medium risk clause (confidence: {top_score:.1%}).",
                        suggested_fix="Consider negotiating more favorable terms for this clause.",
                    ))
        except Exception as e:
            logger.warning(f"Zero-shot classification failed: {e}")

        return findings

    @staticmethod
    def _format_entities(entities: dict) -> str:
        """Format entities dict to readable string."""
        parts = []
        for key, values in entities.items():
            if values:
                parts.append(f"{key}: {', '.join(values[:5])}")
        return "; ".join(parts) if parts else "No entities found"
