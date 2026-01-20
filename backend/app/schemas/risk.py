from pydantic import BaseModel
from typing import Optional


class RiskFindingRead(BaseModel):
    id: str
    issue_type: str
    explanation: str
    recommendation: Optional[str]
    compared_standard_clause: Optional[str]

    class Config:
        orm_mode = True
