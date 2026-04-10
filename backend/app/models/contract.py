import uuid
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base
from app.core.constants import RiskLevel, ContractStatus


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_name = Column(String, nullable=False)

    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    upload_date = Column(DateTime(timezone=True), server_default=func.now())

    overall_risk = Column(Enum(RiskLevel), nullable=True)
    status = Column(Enum(ContractStatus), nullable=False)

    language = Column(String, nullable=False, default="EN")

    def __repr__(self) -> str:
        return f"<Contract id={self.id} file={self.file_name}>"
