from pydantic import BaseModel
from typing import Optional

from app.core.constants import ClauseType, RiskLevel


class ClauseRead(BaseModel):
    id: str
    clause_text: str
    clause_type: ClauseType
    risk_level: Optional[RiskLevel]
    confidence: Optional[float]

    class Config:
        orm_mode = True
