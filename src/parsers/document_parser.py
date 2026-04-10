"""
Document Parsing Module

Supports PDF and DOCX parsing for contract text extraction.
Uses PyMuPDF (fitz) for PDF and python-docx for DOCX.
Falls back gracefully if libraries are not available.
"""

import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def parse_document(file_path: str) -> str:
    """Parse a document and return extracted text.

    Supports: .pdf, .docx, .txt
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return parse_pdf(file_path)
    elif ext == ".docx":
        return parse_docx(file_path)
    elif ext == ".txt":
        return parse_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Supported: .pdf, .docx, .txt")


def parse_pdf(file_path: str) -> str:
    """Extract text from a PDF file using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        text = "\n".join(text_parts)
        if text.strip():
            logger.info(f"Extracted {len(text)} chars from PDF: {file_path}")
            return text
    except ImportError:
        logger.warning("PyMuPDF not available, trying pdfplumber")
    except Exception as e:
        logger.warning(f"PyMuPDF extraction failed: {e}")

    # Fallback to pdfplumber
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        text = "\n".join(text_parts)
        if text.strip():
            logger.info(f"Extracted {len(text)} chars from PDF via pdfplumber: {file_path}")
            return text
    except ImportError:
        logger.warning("pdfplumber not available, trying PyPDF2")
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed: {e}")

    # Fallback to PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        text = "\n".join(text_parts)
        logger.info(f"Extracted {len(text)} chars from PDF via PyPDF2: {file_path}")
        return text
    except ImportError:
        logger.error("No PDF parsing library available (install PyMuPDF, pdfplumber, or PyPDF2)")
    except Exception as e:
        logger.error(f"All PDF extraction methods failed: {e}")

    return ""


def parse_docx(file_path: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    try:
        from docx import Document
        doc = Document(file_path)
        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        text = "\n\n".join(text_parts)
        logger.info(f"Extracted {len(text)} chars from DOCX: {file_path}")
        return text
    except ImportError:
        logger.error("python-docx not available (pip install python-docx)")
        return ""
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        return ""


def parse_txt(file_path: str) -> str:
    """Read a plain text file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        logger.info(f"Read {len(text)} chars from TXT: {file_path}")
        return text
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as f:
            text = f.read()
        return text
    except Exception as e:
        logger.error(f"Text file reading failed: {e}")
        return ""


def detect_language(text: str) -> str:
    """Detect the language of the text."""
    try:
        from langdetect import detect
        lang = detect(text[:5000])
        return lang
    except Exception:
        if any(ord(c) > 0x3000 for c in text[:1000]):
            return "ja"
        return "en"
