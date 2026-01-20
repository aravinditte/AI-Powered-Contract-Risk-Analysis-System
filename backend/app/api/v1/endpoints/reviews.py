from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1.deps import get_current_user
from app.core.security import require_roles, Role

router = APIRouter()


class ReviewRequest(BaseModel):
    clause_id: str
    decision: str  # ACCEPT | OVERRIDE
    comment: str


@router.post(
    "/submit",
    dependencies=[Depends(require_roles([Role.LEGAL, Role.COMPLIANCE]))],
)
def submit_review(
    request: ReviewRequest,
    user=Depends(get_current_user),
):
    """
    Records human decision.
    AI suggestions are NEVER final.
    """

    return {
        "message": "Review recorded",
        "reviewed_by": user["sub"],
        "decision": request.decision,
    }
