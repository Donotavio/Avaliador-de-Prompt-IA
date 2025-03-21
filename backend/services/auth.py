from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from jose import JWTError
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import logging
import time
import os
from dotenv import load_dotenv

from models.user import User
from services.database import get_db
from schemas.token_schema import TokenData, Token
from services.token_security import (
    create_access_token as secure_create_access_token,
    create_refresh_token,
    decode_token as secure_decode_token,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS
)

# Configuração de logging
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()

# OAuth2 scheme para autenticação
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Autentica um usuário verificando email e senha
    
    Args:
        db: Sessão do banco de dados
        email: Email do usuário
        password: Senha do usuário
        
    Returns:
        User se autenticado com sucesso, None caso contrário
    """
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        logger.warning(f"Tentativa de login com email não cadastrado: {email}")
        return None
    
    if not user.verify_password(password):
        logger.warning(f"Senha incorreta para o usuário: {email}")
        return None
    
    logger.info(f"Usuário autenticado com sucesso: {email}")
    return user

def create_tokens_for_user(user: User) -> Token:
    """
    Cria tokens de acesso e refresh para um usuário
    
    Args:
        user: Usuário para o qual criar os tokens
        
    Returns:
        Token: Objeto Token com tokens de acesso e refresh
    """
    user_data = {
        "sub": str(user.id),
        "email": user.email,
        "is_admin": user.is_admin
    }
    
    # Gera o token de acesso com expiração curta
    access_token = secure_create_access_token(user_data)
    
    # Gera o token de refresh com expiração longa
    refresh_token = create_refresh_token(user_data)
    
    # Calcula a expiração do token de acesso para informar ao cliente
    expires_at = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Retorna um objeto Token em vez de um dicionário
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_at=int(expires_at.timestamp()),
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        is_admin=user.is_admin
    )

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Função de compatibilidade para manter código existente funcionando
    Cria um token de acesso JWT
    """
    return secure_create_access_token(data, expires_delta)

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodifica e valida um token JWT
    """
    try:
        return secure_decode_token(token)
    except Exception as e:
        logger.error(f"Erro ao decodificar token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Obtém o usuário autenticado a partir do token JWT
    """
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        token_data = TokenData(user_id=user_id, email=payload.get("email"), is_admin=payload.get("is_admin"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao validar token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível validar as credenciais",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Atualiza timestamp de última atividade
    user.last_activity = datetime.utcnow()
    db.commit()
        
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Verifica se o usuário está ativo
    
    Args:
        current_user: Usuário atual
        
    Returns:
        User: Usuário ativo
        
    Raises:
        HTTPException: Se o usuário estiver inativo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    return current_user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Verifica se o usuário é administrador
    
    Args:
        current_user: Usuário atual
        
    Returns:
        User: Usuário administrador
        
    Raises:
        HTTPException: Se o usuário não for administrador
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão de administrador necessária"
        )
    return current_user

def get_client_ip(request: Request) -> str:
    """
    Extrai o endereço IP real do cliente, considerando proxies
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Pega o primeiro IP (cliente original)
        return forwarded.split(",")[0].strip()
    
    client = request.client.host if request.client else None
    return client or "unknown" 