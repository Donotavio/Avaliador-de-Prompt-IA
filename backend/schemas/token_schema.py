from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    """
    Esquema para representar tokens de autenticação
    """
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_at: Optional[int] = None  # Timestamp de expiração
    user_id: str
    email: str
    full_name: str
    is_admin: bool
    csrf_token: Optional[str] = None  # Token CSRF para proteção contra ataques CSRF

class TokenData(BaseModel):
    """
    Dados decodificados do token JWT
    """
    user_id: Optional[str] = None
    email: Optional[str] = None
    is_admin: Optional[bool] = None
    token_type: Optional[str] = None  # 'access' ou 'refresh'
    exp: Optional[datetime] = None  # Expiração

class RefreshRequest(BaseModel):
    """
    Requisição para obter um novo token de acesso usando o refresh token
    """
    refresh_token: str 