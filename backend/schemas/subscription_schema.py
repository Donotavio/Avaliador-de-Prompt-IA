from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

# Schema para criar uma assinatura
class SubscriptionCreate(BaseModel):
    plan_type: str = Field(default="premium")
    amount: float = Field(...)

# Schema para atualizar status da assinatura
class SubscriptionUpdate(BaseModel):
    status: Optional[str] = None
    abacate_payment_id: Optional[str] = None
    abacate_customer_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

# Schema para resposta de assinatura
class Subscription(BaseModel):
    id: str
    user_id: str
    status: str
    plan_type: str
    amount: float
    currency: str
    abacate_payment_id: Optional[str] = None
    abacate_customer_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True) 