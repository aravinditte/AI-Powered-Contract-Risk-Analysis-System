import uuid
from sqlalchemy import Column, Text, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class RiskFinding(Base):
    __tablename__ = "risk_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    clause_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clauses.id", ondelete="CASCADE"),
        nullable=False,
    )

    issue_type = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)

    compared_standard_clause = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<RiskFinding id={self.id} issue={self.issue_type}>"
