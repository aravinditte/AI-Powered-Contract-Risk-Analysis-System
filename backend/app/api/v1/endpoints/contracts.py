from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from typing import List

from app.api.v1.deps import get_current_user
from app.core.security import require_roles, Role

router = APIRouter()


@router.post(
    "/upload",
    dependencies=[Depends(require_roles([Role.LEGAL, Role.ADMIN]))],
)
def upload_contract(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    """
    Upload a contract file.
    AI analysis is triggered asynchronously later.
    """

    if not file.filename.lower().endswith((".pdf", ".docx", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format",
        )

    return {
        "message": "Contract uploaded successfully",
        "uploaded_by": user["sub"],
        "file_name": file.filename,
    }


@router.get(
    "/{contract_id}",
    dependencies=[Depends(require_roles([
        Role.LEGAL,
        Role.COMPLIANCE,
        Role.MANAGER,
        Role.ADMIN,
    ]))],
)
def get_contract(contract_id: str):
    """
    Retrieve contract metadata and status.
    """
    return {
        "contract_id": contract_id,
        "status": "ANALYZED",
        "overall_risk": "MEDIUM",
    }
