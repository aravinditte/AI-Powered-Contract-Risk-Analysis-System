from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
)
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path

from app.api.v1.deps import get_current_user
from app.core.security import require_roles, Role
from app.db.session import get_db
from app.services.contract_service import create_contract
from app.models.contract import Contract
from app.parsers.pdf_parser import extract_text_from_pdf
from app.parsers.docx_parser import extract_text_from_docx
from app.parsers.text_parser import extract_text_from_txt
from app.ai.pipeline import run_ai_pipeline
from app.services.risk_service import record_risk_finding
from app.utils.file_storage import save_uploaded_file
from app.core.constants import ContractStatus

router = APIRouter()


# -------------------------
# Background AI Task
# -------------------------
def run_ai_analysis(
    contract_id: str,
    contract_text: str,
    user_id: str,
    db: Session,
):
    results = run_ai_pipeline(contract_text)

    for result in results:
        record_risk_finding(
            db=db,
            clause_id=None,  # Clause persistence handled later
            issue_type=result["risk_level"],
            explanation=result["explanation"],
            recommendation=None,
            compared_standard_clause=result.get("compared_standard_clause"),
            user_id=user_id,
        )

    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    contract.status = ContractStatus.ANALYZED
    db.commit()


# -------------------------
# Upload Contract
# -------------------------
@router.post(
    "/upload",
    dependencies=[Depends(require_roles([Role.LEGAL, Role.ADMIN]))],
)
def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    if not file.filename.lower().endswith((".pdf", ".docx", ".txt")):
        raise HTTPException(status_code=400, detail="Unsupported file format")

    stored_path: Path = save_uploaded_file(
        file=file.file.read(),
        original_filename=file.filename,
    )

    # Persist contract
    contract = create_contract(
        db=db,
        file_name=file.filename,
        user_id=user["sub"],
    )

    # Extract text
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(stored_path)
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(stored_path)
    else:
        text = extract_text_from_txt(stored_path)

    # Run AI asynchronously
    background_tasks.add_task(
        run_ai_analysis,
        contract.id,
        text,
        user["sub"],
        db,
    )

    return {
        "contract_id": str(contract.id),
        "status": contract.status,
        "message": "Contract uploaded. AI analysis running.",
    }


# -------------------------
# GET /contracts  ✅ (Dashboard)
# -------------------------
@router.get(
    "",
    dependencies=[Depends(require_roles([
        Role.LEGAL,
        Role.COMPLIANCE,
        Role.MANAGER,
        Role.ADMIN,
    ]))],
)
def list_contracts(db: Session = Depends(get_db)):
    contracts = db.query(Contract).order_by(Contract.upload_date.desc()).all()

    return [
        {
            "id": str(c.id),
            "file_name": c.file_name,
            "status": c.status,
            "overall_risk": c.overall_risk,
            "upload_date": c.upload_date,
        }
        for c in contracts
    ]


# -------------------------
# GET /contracts/{id}
# -------------------------
@router.get(
    "/{contract_id}",
    dependencies=[Depends(require_roles([
        Role.LEGAL,
        Role.COMPLIANCE,
        Role.MANAGER,
        Role.ADMIN,
    ]))],
)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    return {
        "id": str(contract.id),
        "file_name": contract.file_name,
        "status": contract.status,
        "overall_risk": contract.overall_risk,
        "upload_date": contract.upload_date,
    }
