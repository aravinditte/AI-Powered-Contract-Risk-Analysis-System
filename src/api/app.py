"""
FastAPI Backend

Endpoints for:
- Upload contract (PDF/DOCX/TXT)
- Get analysis results
- Submit review decision
- Get review history / audit trail
- Manage templates
- Dashboard statistics
"""

import json
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.db import database as db
from src.parsers.document_parser import parse_document, detect_language
from src.pipeline import AnalysisPipeline

logger = logging.getLogger(__name__)

UPLOAD_DIR = str(Path(__file__).parent.parent.parent / "data" / "uploads")
TEMPLATES_DIR = str(Path(__file__).parent.parent.parent / "data" / "templates")
STATIC_DIR = str(Path(__file__).parent.parent / "static")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app = FastAPI(
    title="AI Contract Risk Analysis System",
    description="3-Layer Hybrid Contract Risk Analysis with Human Review",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the frontend dashboard
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize database on startup
pipeline = AnalysisPipeline(templates_dir=TEMPLATES_DIR)


@app.on_event("startup")
def startup():
    db.init_db()
    logger.info("Database initialized")


# --- Pydantic models ---

class ReviewRequest(BaseModel):
    reviewer_name: str
    decision: str  # "approve" or "reject"
    comments: Optional[str] = ""


class TemplateCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    content: str


# --- Contract Endpoints ---

@app.post("/api/contracts/upload")
async def upload_contract(
    file: UploadFile = File(...),
    template_name: Optional[str] = Form(None),
):
    """Upload a contract file and trigger analysis."""
    allowed_extensions = {".pdf", ".docx", ".txt"}
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {', '.join(allowed_extensions)}")

    # Save uploaded file
    file_id = str(uuid.uuid4())
    saved_filename = f"{file_id}{ext}"
    save_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = os.path.getsize(save_path)

    # Parse document
    try:
        text = parse_document(save_path)
    except Exception as e:
        os.remove(save_path)
        raise HTTPException(400, f"Failed to parse document: {e}")

    if not text.strip():
        os.remove(save_path)
        raise HTTPException(400, "Could not extract text from document")

    # Detect language
    language = detect_language(text)

    # Create contract record
    contract_id = db.create_contract(
        filename=saved_filename,
        original_filename=file.filename or "unknown",
        language=language,
        file_size=file_size,
        text_content=text,
    )

    # Run analysis pipeline
    try:
        report = pipeline.analyze(
            text=text,
            contract_id=contract_id,
            language=language,
            template_name=template_name,
        )

        # Save results
        report_dict = report.to_dict()
        findings_dicts = report_dict.pop("findings", [])

        db.update_contract_analysis(
            contract_id=contract_id,
            overall_risk=report.overall_risk,
            overall_score=report.overall_score,
            report_json=json.dumps(report_dict),
        )

        db.save_findings(contract_id, findings_dicts)

        return {
            "contract_id": contract_id,
            "filename": file.filename,
            "language": language,
            "overall_risk": report.overall_risk,
            "overall_score": report.overall_score,
            "total_findings": report.total_findings,
            "critical_count": report.critical_count,
            "high_count": report.high_count,
            "medium_count": report.medium_count,
            "status": "analyzed",
            "message": "Contract uploaded and analyzed. Pending human review.",
        }

    except Exception as e:
        logger.error(f"Analysis failed for contract {contract_id}: {e}")
        db.update_contract_status(contract_id, "analysis_failed")
        raise HTTPException(500, f"Analysis failed: {e}")


@app.get("/api/contracts")
def list_contracts(
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """List all contracts."""
    contracts = db.list_contracts(status=status, limit=limit, offset=offset)
    # Exclude text_content and report_json from list view for performance
    for c in contracts:
        c.pop("text_content", None)
        c.pop("report_json", None)
    return {"contracts": contracts, "count": len(contracts)}


@app.get("/api/contracts/{contract_id}")
def get_contract(contract_id: str):
    """Get contract details with analysis results."""
    contract = db.get_contract(contract_id)
    if not contract:
        raise HTTPException(404, "Contract not found")

    findings = db.get_findings(contract_id)
    reviews = db.get_reviews(contract_id)

    report = None
    if contract.get("report_json"):
        try:
            report = json.loads(contract["report_json"])
        except json.JSONDecodeError:
            pass

    contract.pop("text_content", None)
    contract.pop("report_json", None)

    return {
        "contract": contract,
        "findings": findings,
        "reviews": reviews,
        "report": report,
    }


@app.get("/api/contracts/{contract_id}/findings")
def get_contract_findings(contract_id: str):
    """Get analysis findings for a contract."""
    contract = db.get_contract(contract_id)
    if not contract:
        raise HTTPException(404, "Contract not found")
    findings = db.get_findings(contract_id)
    return {"contract_id": contract_id, "findings": findings, "count": len(findings)}


# --- Review Endpoints ---

@app.post("/api/reviews/{contract_id}")
def submit_review(contract_id: str, review: ReviewRequest):
    """Submit a human review decision for a contract."""
    contract = db.get_contract(contract_id)
    if not contract:
        raise HTTPException(404, "Contract not found")

    if review.decision not in ("approve", "reject"):
        raise HTTPException(400, "Decision must be 'approve' or 'reject'")

    review_id = db.create_review(
        contract_id=contract_id,
        reviewer_name=review.reviewer_name,
        decision=review.decision,
        comments=review.comments or "",
    )

    return {
        "review_id": review_id,
        "contract_id": contract_id,
        "decision": review.decision,
        "message": f"Contract {review.decision}d by {review.reviewer_name}.",
    }


@app.get("/api/reviews")
def get_pending_reviews():
    """Get all contracts pending review."""
    pending = db.get_pending_reviews()
    for c in pending:
        c.pop("text_content", None)
        c.pop("report_json", None)
    return {"pending_reviews": pending, "count": len(pending)}


@app.get("/api/reviews/{contract_id}/history")
def get_review_history(contract_id: str):
    """Get review history for a contract."""
    reviews = db.get_reviews(contract_id)
    return {"contract_id": contract_id, "reviews": reviews}


# --- Audit Trail ---

@app.get("/api/audit")
def get_audit_log(
    contract_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get audit trail."""
    entries = db.get_audit_log(contract_id=contract_id, limit=limit, offset=offset)
    return {"audit_log": entries, "count": len(entries)}


# --- Template Management ---

@app.get("/api/templates")
def list_templates():
    """List all active templates."""
    templates = db.list_templates()
    for t in templates:
        t.pop("content", None)
    return {"templates": templates, "count": len(templates)}


@app.post("/api/templates")
def create_template(template: TemplateCreate):
    """Create a new approved template."""
    # Save to database
    template_id = db.create_template(
        name=template.name,
        content=template.content,
        description=template.description or "",
    )

    # Also save as file for the comparator
    template_path = os.path.join(TEMPLATES_DIR, f"{template.name}.txt")
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(template.content)

    return {
        "template_id": template_id,
        "name": template.name,
        "message": "Template created successfully.",
    }


@app.get("/api/templates/{template_id}")
def get_template(template_id: str):
    """Get a template by ID."""
    template = db.get_template(template_id)
    if not template:
        raise HTTPException(404, "Template not found")
    return template


@app.delete("/api/templates/{template_id}")
def delete_template(template_id: str):
    """Delete (deactivate) a template."""
    template = db.get_template(template_id)
    if not template:
        raise HTTPException(404, "Template not found")
    db.delete_template(template_id)
    return {"message": "Template deleted.", "template_id": template_id}


# --- Statistics ---

@app.get("/api/statistics")
def get_statistics():
    """Get dashboard statistics."""
    return db.get_statistics()


# --- Health Check ---

@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0", "architecture": "3-layer-hybrid"}
