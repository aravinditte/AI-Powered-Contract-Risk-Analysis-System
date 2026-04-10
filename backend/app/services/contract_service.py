from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.core.constants import ContractStatus
from app.models.audit_log import AuditLog
from app.core.constants import AuditAction


def create_contract(
    db: Session,
    file_name: str,
    user_id: str,
    language: str = "EN",
) -> Contract:
    contract = Contract(
        file_name=file_name,
        uploaded_by=user_id,
        status=ContractStatus.UPLOADED,
        language=language,
    )

    db.add(contract)
    db.flush()

    audit = AuditLog(
        action=AuditAction.CONTRACT_UPLOADED,
        user_id=user_id,
        target_id=contract.id,
    )
    db.add(audit)

    db.commit()
    return contract
