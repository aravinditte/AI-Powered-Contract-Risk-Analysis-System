# AI-Powered Contract Risk Analysis System

## Overview

An enterprise contract risk analysis platform using a **3-layer hybrid architecture** that ensures **ZERO clauses are missed** and costs **ZERO money** to run (no paid APIs).

The system:
- Uses **deterministic rules** to guarantee every mandatory clause is checked
- Employs **NLP/semantic analysis** with free local models for deeper risk detection
- Optionally uses **local RAG** (Ollama + FAISS) for natural language explanations
- Compares contracts against **approved templates** clause-by-clause
- Provides **explainable results** with confidence scores and cross-validation
- Enforces **mandatory human review** — never auto-approves

**This system NEVER auto-approves contracts.**

---

## Architecture: 3-Layer Hybrid Pipeline

```
Contract Upload (PDF/DOCX/TXT)
         |
         v
  [Document Parser] --> Text Extraction + Language Detection
         |
         v
  +----- LAYER 1: Rule-Based Engine (Deterministic) -----+
  | - Regex pattern matching for ALL 20 mandatory clauses |
  | - Risk keyword scanning (penalty, unlimited, etc.)    |
  | - Structural validation (parties, dates, signatures)  |
  | - NEVER misses a clause - 100% deterministic          |
  +-------------------------------------------------------+
         |
         v
  +----- LAYER 2: NLP/Semantic Analysis (Free Models) ---+
  | - sentence-transformers (all-MiniLM-L6-v2)           |
  | - spaCy NER (parties, dates, amounts, jurisdictions) |
  | - Zero-shot classification for risk levels           |
  | - Ambiguous language & one-sided provision detection  |
  +------------------------------------------------------+
         |
         v
  +----- LAYER 3: RAG with Local LLM (Optional) --------+
  | - FAISS vector store for template knowledge base     |
  | - Ollama integration for natural language explanations|
  | - Graceful fallback if Ollama not available           |
  +------------------------------------------------------+
         |
         v
  [Template Comparator] --> Clause-by-clause diff
         |
         v
  [Cross-Validation] --> Confidence boosting
         |
         v
  [Unified Risk Report] --> Dashboard + Human Review Queue
```

### 20 Mandatory Clauses Checked (English + Japanese)

| # | Clause | Severity if Missing |
|---|--------|-------------------|
| 1 | Governing Law / Jurisdiction | CRITICAL |
| 2 | Termination / Exit | CRITICAL |
| 3 | Payment Terms | CRITICAL |
| 4 | Confidentiality / NDA | HIGH |
| 5 | IP Ownership | HIGH |
| 6 | Liability / Indemnification | CRITICAL |
| 7 | Force Majeure | HIGH |
| 8 | Dispute Resolution | HIGH |
| 9 | Data Protection / Privacy | HIGH |
| 10 | Non-Compete | MEDIUM |
| 11 | Working Hours / Scope | MEDIUM |
| 12 | Tax Obligations | MEDIUM |
| 13 | Insurance | MEDIUM |
| 14 | Amendments | MEDIUM |
| 15 | Notice Provisions | LOW |
| 16 | Severability | LOW |
| 17 | Entire Agreement | LOW |
| 18 | Assignment | MEDIUM |
| 19 | Warranties | MEDIUM |
| 20 | Auto-Renewal | MEDIUM |

### Risk Keywords Scanned

`penalty`, `unlimited liability`, `unilateral`, `waive`, `forfeit`, `sole discretion`, `irrevocable`, `perpetual`, `worldwide`, `non-exclusive`

---

## Tech Stack (ALL FREE)

| Component | Technology | Cost |
|-----------|-----------|------|
| Backend | Python / FastAPI | Free |
| Database | SQLite | Free |
| NLP | spaCy, sentence-transformers | Free |
| Classification | HuggingFace zero-shot (BART) | Free |
| Vector Store | FAISS | Free |
| Local LLM | Ollama (optional) | Free |
| PDF Parsing | PyMuPDF / pdfplumber / PyPDF2 | Free |
| DOCX Parsing | python-docx | Free |
| Frontend | HTML / CSS / JS (no framework) | Free |

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# Clone the repo
cd AI-Powered-Contract-Risk-Analysis-System

# Install dependencies
pip install -r requirements-hybrid.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Initialize the database
python run.py --init-db

# Start the server
python run.py
```

### Access

- **Dashboard**: http://localhost:8000/static/index.html
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

### Optional: Ollama (for Layer 3 LLM explanations)

```bash
# Install Ollama (https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3

# The system auto-detects Ollama and uses it if available
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/contracts/upload` | Upload and analyze a contract |
| GET | `/api/contracts` | List all contracts |
| GET | `/api/contracts/{id}` | Get contract detail with findings |
| GET | `/api/contracts/{id}/findings` | Get findings for a contract |
| POST | `/api/reviews/{id}` | Submit review decision |
| GET | `/api/reviews` | Get pending reviews |
| GET | `/api/reviews/{id}/history` | Get review history |
| GET | `/api/audit` | Get audit trail |
| GET | `/api/templates` | List templates |
| POST | `/api/templates` | Create template |
| GET | `/api/templates/{id}` | Get template |
| DELETE | `/api/templates/{id}` | Delete template |
| GET | `/api/statistics` | Dashboard statistics |
| GET | `/api/health` | Health check |

---

## Explainable Results

Every finding includes:
- **Detecting layer**: `rule_based`, `nlp_semantic`, `rag`, or `template_comparison`
- **Confidence score**: 0-100%
- **Clause text**: The specific text that triggered the finding
- **Explanation**: Why it's risky
- **Suggested fix**: Recommended remediation
- **Severity**: CRITICAL / HIGH / MEDIUM / LOW / INFO
- **Cross-validation**: Boosted confidence when multiple layers agree

---

## Human Review Enforcement

- System NEVER auto-approves
- Every analyzed contract enters a review queue
- Reviewers must explicitly approve or reject
- Full audit trail with timestamps
- SQLite backend for persistence

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run only rule-based tests
pytest tests/test_rule_based.py -v

# Run pipeline tests
pytest tests/test_pipeline.py -v
```

---

## Project Structure

```
src/
├── analyzers/
│   ├── rule_based.py          # Layer 1: Deterministic rule engine
│   ├── nlp_analyzer.py        # Layer 2: NLP/Semantic analysis
│   ├── rag_analyzer.py        # Layer 3: RAG with FAISS + Ollama
│   └── template_comparator.py # Template comparison engine
├── parsers/
│   └── document_parser.py     # PDF/DOCX/TXT parsing
├── db/
│   └── database.py            # SQLite database layer
├── api/
│   └── app.py                 # FastAPI application
├── static/
│   └── index.html             # Frontend dashboard
└── pipeline.py                # Orchestrator pipeline

data/
├── templates/                 # Approved template contracts
├── uploads/                   # Uploaded contract files
└── contracts.db               # SQLite database

tests/
├── test_rule_based.py         # Rule engine tests
└── test_pipeline.py           # Pipeline integration tests
```

---

## Key Principles

- **Zero Cost**: All models run locally, no API calls
- **Zero Missed Clauses**: Rule-based layer is deterministic
- **Explainable AI**: Every finding has a clear explanation
- **Human-in-the-Loop**: Mandatory review, never auto-approve
- **Audit-Ready**: Full audit trail for compliance
- **Bilingual**: English and Japanese support
- **Graceful Degradation**: Works without Ollama, spaCy, or ML models
