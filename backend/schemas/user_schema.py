from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime

# Schema para criar um usuário
class UserBase(BaseModel):
    """Esquema base para usuários"""
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    """Esquema para criação de usuários"""
    password: str
    tax_id: Optional[str] = None  # CPF ou CNPJ
    phone: Optional[str] = None   # Telefone com DDD

# Schema para atualizar um usuário
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None

# Schema para resposta de usuário (sem senha)
class User(UserBase):
    """Esquema para representação de usuários existentes"""
    id: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime
    abacate_customer_id: Optional[str] = None

    class Config:
        orm_mode = True

# Schema para login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(User):
    """Esquema para usuários no banco de dados (inclui senha hash)"""
    hashed_password: str 