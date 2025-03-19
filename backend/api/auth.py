from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from typing import Any, Dict
import logging
import re

from services.database import get_db
from models.user import User
from schemas.user_schema import UserCreate, User as UserSchema
from schemas.token_schema import Token
from services.auth import authenticate_user, create_access_token, get_current_user
from services.abacate_pay import AbacatePayClient

router = APIRouter(prefix="/auth", tags=["authentication"])

# Configuração de logging
logger = logging.getLogger(__name__)

# Cliente do AbacatePay
abacate_pay_client = AbacatePayClient()

def sanitize_cpf_cnpj(value: str) -> str:
    """
    Remove caracteres não numéricos de CPF/CNPJ
    """
    return re.sub(r'[^0-9]', '', value) if value else ''

def format_phone(value: str) -> str:
    """
    Formata número de telefone para o padrão esperado pelo AbacatePay
    """
    cleaned = re.sub(r'[^0-9]', '', value) if value else ''
    if len(cleaned) >= 10:
        # Formato com DDD e número
        return cleaned
    return cleaned

@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Retorna o perfil do usuário autenticado
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin
    }

@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    Registra um novo usuário e cria cliente no AbacatePay
    """
    try:
        # Verifica se o email está em um formato válido
        if "@" not in user_data.email or "." not in user_data.email.split("@")[1]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Email inválido. Informe um endereço de email no formato correto (ex: nome@dominio.com)"
            )
        
        # Verifica se o email já está em uso
        db_user = db.query(User).filter(User.email == user_data.email).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já está em uso"
            )
        
        # Cria o usuário
        new_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=User.get_password_hash(user_data.password)
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"Usuário registrado com sucesso: {user_data.email}")
        
        # Tenta criar o cliente no AbacatePay (não impede a criação local se falhar)
        try:
            # Prepara os dados do cliente para AbacatePay
            abacate_customer_data = {
                "name": user_data.full_name,
                "email": user_data.email,
                "taxId": sanitize_cpf_cnpj(user_data.tax_id) if hasattr(user_data, 'tax_id') and user_data.tax_id else "00000000000",
                "cellphone": format_phone(user_data.phone) if hasattr(user_data, 'phone') and user_data.phone else "11999999999"
            }
            
            # Verifica se o cliente AbacatePay está inicializado corretamente
            if not hasattr(abacate_pay_client, 'api_key') or not abacate_pay_client.api_key:
                logger.warning("API Key do AbacatePay não configurada. Ignorando criação do cliente.")
                return new_user
            
            # Cria o cliente no AbacatePay
            abacate_response = abacate_pay_client.create_customer(abacate_customer_data)
            
            # Atualiza o usuário com o ID do cliente no AbacatePay
            if abacate_response and "id" in abacate_response:
                new_user.abacate_customer_id = abacate_response["id"]
                db.commit()
                logger.info(f"Cliente AbacatePay criado com sucesso para o usuário {user_data.email}")
            
        except Exception as e:
            # Apenas loga o erro mas não impede o fluxo principal
            logger.error(f"Erro ao criar cliente no AbacatePay: {str(e)}")
        
        return new_user
        
    except OperationalError as e:
        logger.error(f"Erro de conexão com o banco de dados: {str(e)}")
        db.rollback()  # Desfaz qualquer transação pendente
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Erro de conexão com o banco de dados. Por favor, tente novamente mais tarde."
        )
    except SQLAlchemyError as e:
        logger.error(f"Erro no banco de dados: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao registrar usuário. Por favor, tente novamente."
        )
    except Exception as e:
        logger.error(f"Erro inesperado ao registrar usuário: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor. Por favor, tente novamente mais tarde."
        )

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Login OAuth2 com username e password
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Cria token JWT
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_admin": user.is_admin
    } 