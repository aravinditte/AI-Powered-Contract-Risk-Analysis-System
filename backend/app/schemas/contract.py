from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.core.constants import RiskLevel, ContractStatus


class ContractBase(BaseModel):
    file_name: str
    language: str


class ContractCreate(ContractBase):
    pass


class ContractRead(ContractBase):
    id: str
    upload_date: datetime
    overall_risk: Optional[RiskLevel]
    status: ContractStatus

    class Config:
        orm_mode = True
