from sqlalchemy import Boolean, Column, String, DateTime, Integer, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from services.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, active, expired, cancelled
    plan_type = Column(String(50), nullable=False, default="premium")
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="BRL")
    abacate_payment_id = Column(String(255), nullable=True)
    abacate_customer_id = Column(String(255), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # Relacionamento com o usuário
    user = relationship("User", backref="subscriptions")
    
    def is_active(self) -> bool:
        """Verifica se a assinatura está ativa"""
        if self.status != "active":
            return False
        
        # Verifica se a data de término é no futuro
        now = datetime.now()
        if self.end_date and self.end_date < now:
            return False
            
        return True 