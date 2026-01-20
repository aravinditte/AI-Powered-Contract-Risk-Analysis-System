from pydantic import BaseModel


class UserRead(BaseModel):
    id: str
    username: str
    role: str
    is_active: bool

    class Config:
        orm_mode = True
