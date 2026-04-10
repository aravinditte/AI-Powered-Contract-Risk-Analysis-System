import uuid
from sqlalchemy import Column, Text, Enum, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base
from app.core.constants import ClauseType, RiskLevel


class Clause(Base):
    __tablename__ = "clauses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    contract_id = Column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
    )

    clause_text = Column(Text, nullable=False)

    clause_type = Column(Enum(ClauseType), nullable=False)

    risk_level = Column(Enum(RiskLevel), nullable=True)

    confidence = Column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<Clause id={self.id} type={self.clause_type}>"
