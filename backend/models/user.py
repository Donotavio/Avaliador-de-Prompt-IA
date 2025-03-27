from sqlalchemy import Boolean, Column, String, DateTime, Integer, JSON
from sqlalchemy.sql import func
from passlib.context import CryptContext
import uuid
from datetime import datetime
import logging

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
    
    # Campos para verificação de email
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(6), nullable=True)
    email_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Rastreamento de sessão para segurança
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    active_tokens = Column(JSON, default=list)
    
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
    
    # Campos para recuperação de senha
    reset_password_token = Column(String(255), nullable=True, index=True)
    reset_password_expires = Column(DateTime(timezone=True), nullable=True)

    def verify_password(self, password: str) -> bool:
        """Verifica se a senha fornecida corresponde à senha hash armazenada"""
        try:
            return pwd_context.verify(password, self.hashed_password)
        except Exception as e:
            # Registra o erro e propaga a exceção para evitar verificações inseguras
            logger = logging.getLogger(__name__)
            logger.error(f"Erro crítico ao verificar senha: {str(e)}")
            
            # Não retornamos False como fallback, em vez disso lançamos exceção
            # para garantir que a segurança não seja comprometida
            raise RuntimeError("Falha crítica na verificação de senha") from e
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Gera um hash para a senha"""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            # Registra o erro e propaga a exceção para evitar senhas fracas
            logger = logging.getLogger(__name__)
            logger.error(f"Erro crítico ao gerar hash de senha: {str(e)}")
            
            # Não utilizamos o fallback inseguro, em vez disso lançamos exceção
            # para garantir que a segurança não seja comprometida
            raise RuntimeError("Falha crítica na criptografia de senha") from e 