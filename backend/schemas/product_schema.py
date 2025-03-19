from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Schema para criar um produto
class ProductCreate(BaseModel):
    """Schema para criação de produtos"""
    external_id: str
    name: str
    description: Optional[str] = None
    price_in_cents: int
    active: bool = True
    recurrence_period_days: int = 30

# Schema para atualizar um produto
class ProductUpdate(BaseModel):
    """Schema para atualização de produtos"""
    name: Optional[str] = None
    description: Optional[str] = None
    price_in_cents: Optional[int] = None
    active: Optional[bool] = None
    recurrence_period_days: Optional[int] = None

# Schema para representação de produtos
class Product(BaseModel):
    """Schema para representação de produtos"""
    id: str
    external_id: str
    name: str
    description: Optional[str] = None
    price_in_cents: int
    price: float  # Campo calculado para preço em reais
    active: bool
    recurrence_period_days: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 