"""
Layer 3: Local RAG with Ollama Integration

Uses FAISS for local vector store and Ollama for natural language explanations.
Indexes company-approved templates as a knowledge base.
Graceful fallback if Ollama is not available.

ZERO API cost — everything runs locally.
"""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_faiss_index = None
_sentence_model = None


@dataclass
class RAGFinding:
    clause_type: str
    severity: str
    confidence: float
    clause_text: str
    explanation: str
    suggested_fix: str
    detecting_layer: str = "rag"
    similar_templates: Optional[list[dict]] = None


def _get_sentence_model():
    """Get or load the sentence transformer model."""
    global _sentence_model
    if _sentence_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("RAG: Loaded sentence-transformers model")
        except Exception as e:
            logger.warning(f"RAG: Could not load sentence-transformers: {e}")
            _sentence_model = False
    return _sentence_model if _sentence_model is not False else None


class VectorStore:
    """Simple FAISS-based vector store for template clauses."""

    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = None
        self.documents: list[dict] = []
        self._init_faiss()

    def _init_faiss(self):
        """Initialize FAISS index."""
        try:
            import faiss
            self.index = faiss.IndexFlatIP(self.dimension)
            logger.info("FAISS index initialized")
        except ImportError:
            logger.warning("FAISS not available. Vector store disabled.")
            self.index = None

    def add_documents(self, docs: list[dict], embeddings: np.ndarray):
        """Add documents with their embeddings to the index."""
        if self.index is None:
            return
        import faiss
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
        self.documents.extend(docs)

    def search(self, query_embedding: np.ndarray, top_k: int = 3) -> list[dict]:
        """Search for most similar documents."""
        if self.index is None or self.index.ntotal == 0:
            return []
        import faiss
        query = query_embedding.reshape(1, -1).astype("float32")
        faiss.normalize_L2(query)
        scores, indices = self.index.search(query, min(top_k, self.index.ntotal))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents) and idx >= 0:
                result = self.documents[idx].copy()
                result["similarity_score"] = float(score)
                results.append(result)
        return results

    def save(self, path: str):
        """Save index and documents to disk."""
        if self.index is None:
            return
        import faiss
        faiss.write_index(self.index, f"{path}.faiss")
        with open(f"{path}.json", "w") as f:
            json.dump(self.documents, f)

    def load(self, path: str) -> bool:
        """Load index and documents from disk."""
        try:
            import faiss
            if os.path.exists(f"{path}.faiss") and os.path.exists(f"{path}.json"):
                self.index = faiss.read_index(f"{path}.faiss")
                with open(f"{path}.json") as f:
                    self.documents = json.load(f)
                logger.info(f"Loaded vector store with {len(self.documents)} documents")
                return True
        except Exception as e:
            logger.warning(f"Could not load vector store: {e}")
        return False


class OllamaClient:
    """Simple Ollama integration for local LLM explanations."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model
        self._available = None

    def is_available(self) -> bool:
        """Check if Ollama is running."""
        if self._available is not None:
            return self._available
        try:
            import urllib.request
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                self._available = resp.status == 200
        except Exception:
            self._available = False
            logger.info("Ollama not available — will use structured explanations instead.")
        return self._available

    def generate(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Generate text using Ollama."""
        if not self.is_available():
            return None
        try:
            import urllib.request
            data = json.dumps({
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.3},
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("response", "")
        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
            return None


class RAGAnalyzer:
    """Layer 3: RAG-based analysis with local vector store and optional Ollama."""

    def __init__(self, templates_dir: Optional[str] = None):
        self.vector_store = VectorStore()
        self.ollama = OllamaClient()
        self.templates_dir = templates_dir or str(
            Path(__file__).parent.parent.parent / "data" / "templates"
        )
        self._indexed = False

    def index_templates(self, template_clauses: Optional[list[dict]] = None):
        """Index template clauses into the vector store."""
        model = _get_sentence_model()
        if model is None:
            logger.warning("Cannot index templates without sentence-transformers")
            return

        if template_clauses is None:
            template_clauses = self._load_template_clauses()

        if not template_clauses:
            logger.info("No template clauses to index")
            return

        texts = [c["text"] for c in template_clauses]
        embeddings = model.encode(texts, show_progress_bar=False).astype("float32")
        self.vector_store.add_documents(template_clauses, embeddings)
        self._indexed = True
        logger.info(f"Indexed {len(template_clauses)} template clauses")

    def _load_template_clauses(self) -> list[dict]:
        """Load template clauses from the templates directory."""
        clauses = []
        templates_path = Path(self.templates_dir)
        if not templates_path.exists():
            return clauses

        for template_file in templates_path.glob("*.txt"):
            content = template_file.read_text(encoding="utf-8")
            sections = self._split_template_sections(content)
            for section in sections:
                clauses.append({
                    "text": section["text"],
                    "clause_type": section.get("type", "general"),
                    "template_name": template_file.stem,
                    "source": str(template_file),
                })
        return clauses

    def _split_template_sections(self, text: str) -> list[dict]:
        """Split a template into sections/clauses."""
        import re
        sections = []
        pattern = r"(?:^|\n)(\d+[\.\)]\s+[A-Z][^\n]+)\n"
        matches = list(re.finditer(pattern, text))

        if not matches:
            chunks = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
            return [{"text": c, "type": "general"} for c in chunks]

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()
            section_type = self._infer_clause_type(match.group(1))
            if len(section_text) > 20:
                sections.append({"text": section_text, "type": section_type})

        return sections

    def _infer_clause_type(self, heading: str) -> str:
        """Infer clause type from section heading."""
        heading_lower = heading.lower()
        type_map = {
            "govern": "governing_law", "jurisdict": "governing_law",
            "terminat": "termination", "cancel": "termination",
            "payment": "payment_terms", "fee": "payment_terms", "compensat": "payment_terms",
            "confidential": "confidentiality", "non-disclosure": "confidentiality",
            "intellectual": "ip_ownership", "copyright": "ip_ownership",
            "liabilit": "liability", "indemnif": "liability",
            "force majeure": "force_majeure",
            "dispute": "dispute_resolution", "arbitrat": "dispute_resolution",
            "data protect": "data_protection", "privacy": "data_protection",
            "non-compet": "non_compete",
            "scope": "working_hours", "deliverable": "working_hours",
            "tax": "tax_obligations",
            "insurance": "insurance",
            "amendment": "amendments", "modif": "amendments",
            "notice": "notice",
            "severab": "severability",
            "entire agreement": "entire_agreement",
            "assign": "assignment",
            "warrant": "warranties", "represent": "warranties",
            "renew": "auto_renewal",
        }
        for keyword, clause_type in type_map.items():
            if keyword in heading_lower:
                return clause_type
        return "general"

    def analyze(self, text: str, clauses: Optional[list[str]] = None) -> list[RAGFinding]:
        """Run RAG analysis: find similar templates, optionally explain with Ollama."""
        findings = []

        if not self._indexed:
            self.index_templates()

        model = _get_sentence_model()
        if model is None or self.vector_store.index is None:
            return findings

        text_clauses = clauses or self._split_text_into_clauses(text)

        for clause in text_clauses:
            if len(clause.strip()) < 20:
                continue

            embedding = model.encode(clause, show_progress_bar=False).astype("float32")
            similar = self.vector_store.search(embedding, top_k=3)

            if similar:
                best = similar[0]
                score = best["similarity_score"]

                if score < 0.5:
                    severity = "HIGH"
                    explanation = (
                        f"This clause significantly deviates from approved templates. "
                        f"Nearest match (similarity: {score:.1%}): {best.get('clause_type', 'unknown')} "
                        f"from template '{best.get('template_name', 'unknown')}'."
                    )
                elif score < 0.7:
                    severity = "MEDIUM"
                    explanation = (
                        f"This clause partially matches approved templates. "
                        f"Nearest match (similarity: {score:.1%}): {best.get('clause_type', 'unknown')} "
                        f"from template '{best.get('template_name', 'unknown')}'."
                    )
                else:
                    continue

                llm_explanation = self._get_llm_explanation(clause, best.get("text", ""))

                findings.append(RAGFinding(
                    clause_type=f"template_deviation_{best.get('clause_type', 'unknown')}",
                    severity=severity,
                    confidence=round(score * 100, 1),
                    clause_text=clause[:300],
                    explanation=llm_explanation or explanation,
                    suggested_fix=f"Consider using approved template language: '{best.get('text', '')[:200]}...'",
                    similar_templates=similar,
                ))

        return findings

    def _get_llm_explanation(self, clause: str, template_clause: str) -> Optional[str]:
        """Get natural language explanation from Ollama if available."""
        prompt = (
            f"Compare this contract clause with the approved template version and explain the key differences and risks.\n\n"
            f"Contract clause:\n{clause[:500]}\n\n"
            f"Approved template:\n{template_clause[:500]}\n\n"
            f"Briefly explain the differences and any risks (2-3 sentences):"
        )
        return self.ollama.generate(prompt)

    def _split_text_into_clauses(self, text: str) -> list[str]:
        """Simple clause splitting for RAG analysis."""
        import re
        paragraphs = re.split(r"\n\s*\n", text)
        clauses = []
        for p in paragraphs:
            p = p.strip()
            if len(p) > 30:
                clauses.append(p)
        return clauses

    def suggest_alternative(self, clause_text: str) -> Optional[str]:
        """Suggest alternative clause language using Ollama or template matching."""
        model = _get_sentence_model()
        if model is not None and self.vector_store.index is not None and self.vector_store.index.ntotal > 0:
            embedding = model.encode(clause_text, show_progress_bar=False).astype("float32")
            similar = self.vector_store.search(embedding, top_k=1)
            if similar and similar[0]["similarity_score"] > 0.3:
                template_text = similar[0]["text"]
                llm_suggestion = self.ollama.generate(
                    f"Given this contract clause:\n{clause_text[:300]}\n\n"
                    f"And this approved template version:\n{template_text[:300]}\n\n"
                    f"Suggest improved clause language that addresses risks while being fair to both parties (provide only the clause text):"
                )
                return llm_suggestion or template_text

        return None
