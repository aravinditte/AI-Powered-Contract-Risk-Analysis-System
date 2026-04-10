from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.core.constants import AuditAction


def submit_review(
    db: Session,
    clause_id: str,
    decision: str,
    comment: str,
    user_id: str,
):
    action = (
        AuditAction.REVIEW_ACCEPTED
        if decision == "ACCEPT"
        else AuditAction.REVIEW_OVERRIDDEN
    )

    audit = AuditLog(
        action=action,
        user_id=user_id,
        target_id=clause_id,
        details=comment,
    )

    db.add(audit)
    db.commit()

    return audit
