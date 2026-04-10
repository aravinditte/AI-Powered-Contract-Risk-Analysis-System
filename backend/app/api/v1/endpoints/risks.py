from fastapi import APIRouter, Depends

from app.api.v1.deps import get_current_user
from app.core.security import require_roles, Role

router = APIRouter()


@router.get(
    "/contract/{contract_id}",
    dependencies=[Depends(require_roles([
        Role.LEGAL,
        Role.COMPLIANCE,
        Role.MANAGER,
        Role.ADMIN,
    ]))],
)
def get_contract_risks(contract_id: str):
    """
    Returns AI-detected risks with explanations.
    No approval actions allowed here.
    """

    return {
        "contract_id": contract_id,
        "risks": [
            {
                "clause": "Limitation of Liability",
                "risk_level": "HIGH",
                "confidence": 0.87,
                "explanation": "Deviation from company-approved liability clause.",
            }
        ],
    }
