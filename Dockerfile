# ============================================================
# AI Contract Risk Analysis System — Backend (Main App)
# Uses: FastAPI + SQLite + local AI models (no external DB)
# ============================================================

FROM python:3.11-slim

# --- System dependencies ---
# tesseract-ocr  : OCR for scanned PDFs
# poppler-utils  : pdf2image / pdfplumber support
# gcc / libgomp1 : required by torch & faiss
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    gcc \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Install Python dependencies ---
COPY requirements-hybrid.txt ./
RUN pip install --no-cache-dir -r requirements-hybrid.txt

# Download spaCy English model (used by NLP analyzer)
RUN python -m spacy download en_core_web_sm || true

# --- Copy source code ---
COPY src/        ./src/
COPY templates/  ./templates/
COPY run.py      ./run.py

# Ensure persistent data directories exist
RUN mkdir -p data/uploads data/templates

# Expose FastAPI port
EXPOSE 8000

# Health-check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Start server
CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8000"]
