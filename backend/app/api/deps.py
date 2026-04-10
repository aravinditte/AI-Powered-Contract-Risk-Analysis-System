from fastapi import Depends
from typing import Dict

from app.core.security import decode_token, oauth2_scheme


def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Returns decoded JWT payload.
    Used across all secured endpoints.
    """
    return decode_token(token)
