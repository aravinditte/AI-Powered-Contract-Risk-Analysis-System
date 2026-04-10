from sqlalchemy.orm import Session

from app.models.risk_finding import RiskFinding
from app.models.audit_log import AuditLog
from app.core.constants import AuditAction


def record_risk_finding(
    db: Session,
    clause_id: str,
    issue_type: str,
    explanation: str,
    recommendation: str | None,
    compared_standard_clause: str | None,
    user_id: str,
):
    finding = RiskFinding(
        clause_id=clause_id,
        issue_type=issue_type,
        explanation=explanation,
        recommendation=recommendation,
        compared_standard_clause=compared_standard_clause,
    )

    db.add(finding)

    audit = AuditLog(
        action=AuditAction.AI_ANALYSIS_COMPLETED,
        user_id=user_id,
        target_id=clause_id,
    )

    db.add(audit)
    db.commit()

    return finding
