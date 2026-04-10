from pydantic import BaseModel, Field
from typing import Literal


class ReviewSubmit(BaseModel):
    clause_id: str
    decision: Literal["ACCEPT", "OVERRIDE"]
    comment: str = Field(..., min_length=5)
