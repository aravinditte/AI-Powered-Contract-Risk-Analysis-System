from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.contract import Contract
from app.models.clause import Clause
from app.models.audit_log import AuditLog


def generate_summary_report(db: Session) -> dict:
    return {
        "total_contracts": db.query(func.count(Contract.id)).scalar(),
        "total_clauses": db.query(func.count(Clause.id)).scalar(),
        "total_audit_events": db.query(func.count(AuditLog.id)).scalar(),
    }
