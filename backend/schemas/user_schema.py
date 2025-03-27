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

# Schema para representação completa de usuários
class User(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    is_admin: bool
    is_email_verified: bool = False
    abacate_customer_id: Optional[str] = None
    phone: Optional[str] = None
    tax_id: Optional[str] = None
    
    # Campos de endereço
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_complement: Optional[str] = None
    address_neighborhood: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_postal_code: Optional[str] = None
    address_country: Optional[str] = None
    
    # Método de pagamento preferido
    preferred_payment_method: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Schema para login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(User):
    """Esquema para usuários no banco de dados (inclui senha hash)"""
    hashed_password: str

# Schema para recuperação de senha
class PasswordRecovery(BaseModel):
    """Esquema para solicitação de recuperação de senha"""
    email: EmailStr
    frontend_url: str = Field(..., description="URL base do frontend para redirecionar o usuário")

# Schema para redefinição de senha
class PasswordReset(BaseModel):
    """Esquema para redefinição de senha"""
    token: str = Field(..., description="Token de recuperação enviado por e-mail")
    new_password: str = Field(..., min_length=8, description="Nova senha do usuário (mínimo 8 caracteres)")

# Schema para verificação de e-mail
class EmailVerification(BaseModel):
    """Esquema para verificação de e-mail"""
    token: str = Field(..., description="Token de verificação enviado por e-mail")
    user_id: str = Field(..., description="ID do usuário")

# Schema para reenvio de token de verificação
class ResendVerification(BaseModel):
    """Esquema para reenvio de token de verificação"""
    user_id: str = Field(..., description="ID do usuário") 