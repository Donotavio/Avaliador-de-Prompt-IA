from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    email: str
    full_name: str
    is_admin: bool

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    is_admin: Optional[bool] = None 