import uuid
from sqlalchemy import Column, DateTime, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base
from app.core.constants import AuditAction


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    action = Column(String, nullable=False)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    target_id = Column(UUID(as_uuid=True), nullable=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    details = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<AuditLog action={self.action} user={self.user_id}>"
