from sqlalchemy import Boolean, Column, String, DateTime, Integer
from sqlalchemy.sql import func
from passlib.context import CryptContext
import uuid
from datetime import datetime

from services.database import Base

# Contexto para encriptar senhas com mais opções e configurações de fallback
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Controla a complexidade do hash
    bcrypt__ident="2b"  # Usa a versão compatível 2b
)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())
    
    # ID do cliente no serviço de pagamento AbacatePay
    abacate_customer_id = Column(String(255), nullable=True)
    
    # Campos para informações básicas do usuário
    phone = Column(String(20), nullable=True)
    tax_id = Column(String(20), nullable=True)  # CPF ou CNPJ
    
    # Campos para endereço completo
    address_street = Column(String(255), nullable=True)
    address_number = Column(String(20), nullable=True)
    address_complement = Column(String(100), nullable=True)
    address_neighborhood = Column(String(100), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_state = Column(String(2), nullable=True)
    address_postal_code = Column(String(10), nullable=True)
    address_country = Column(String(2), default="BR")
    
    # Método de pagamento preferido
    preferred_payment_method = Column(String(20), nullable=True)  # PIX, CREDIT_CARD, BOLETO

    def verify_password(self, password: str) -> bool:
        """Verifica se a senha fornecida corresponde à senha hash armazenada"""
        try:
            return pwd_context.verify(password, self.hashed_password)
        except Exception as e:
            print(f"Erro ao verificar senha: {str(e)}")
            # Fallback para casos de erro no bcrypt
            return False
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Gera um hash para a senha"""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            print(f"Erro ao gerar hash: {str(e)}")
            # Fallback para um método alternativo em caso de erro
            import hashlib
            salt = uuid.uuid4().hex
            return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt 