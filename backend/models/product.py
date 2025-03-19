from sqlalchemy import Boolean, Column, String, DateTime, Integer, Text
from sqlalchemy.sql import func
import uuid

from services.database import Base

class Product(Base):
    """
    Modelo para produtos disponíveis para compra
    """
    __tablename__ = "products"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    external_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price_in_cents = Column(Integer, nullable=False)
    active = Column(Boolean, default=True)
    recurrence_period_days = Column(Integer, default=30)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    @property
    def price(self):
        """Retorna o preço em reais"""
        return self.price_in_cents / 100
    
    def to_dict(self):
        """Converte o produto em um dicionário para API"""
        return {
            "id": self.id,
            "external_id": self.external_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "price_in_cents": self.price_in_cents,
            "active": self.active,
            "recurrence_period_days": self.recurrence_period_days
        } 