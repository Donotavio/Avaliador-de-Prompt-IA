from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from typing import Any, Dict
import logging
import re
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from services.database import get_db
from models.user import User
from schemas.user_schema import UserCreate, User as UserSchema, PasswordRecovery, PasswordReset
from schemas.token_schema import Token
from services.auth import authenticate_user, create_access_token, get_current_user
from services.abacate_pay import AbacatePayClient

# Carrega variáveis de ambiente
load_dotenv()

# Obtém configurações de e-mail
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "no-reply@example.com")

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

def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Envia um e-mail com o conteúdo especificado
    """
    if not EMAIL_USER or not EMAIL_PASSWORD:
        logger.error("Configurações de e-mail não definidas")
        return False
    
    try:
        message = MIMEMultipart()
        message["From"] = EMAIL_FROM
        message["To"] = to_email
        message["Subject"] = subject
        
        # Adiciona o corpo HTML
        message.attach(MIMEText(html_content, "html"))
        
        # Conecta ao servidor SMTP
        if EMAIL_PORT == 465:
            # Usar conexão SSL direta para porta 465
            server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
        else:
            # Usar TLS para outras portas (como 587)
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
            server.starttls()
            
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # Envia o e-mail
        server.send_message(message)
        server.quit()
        
        logger.info(f"E-mail enviado para {to_email}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {str(e)}")
        return False

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

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(recovery_data: PasswordRecovery, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Inicia processo de recuperação de senha para um usuário
    """
    # Procura usuário pelo e-mail
    user = db.query(User).filter(User.email == recovery_data.email).first()
    
    # Mesmo que o usuário não exista, retornamos sucesso para evitar 
    # a descoberta de e-mails válidos (proteção contra enumeração)
    if not user:
        logger.info(f"Tentativa de recuperação para e-mail não cadastrado: {recovery_data.email}")
        return {"message": "Se o e-mail estiver cadastrado, você receberá instruções para recuperar sua senha."}
    
    # Gera um token único para recuperação de senha
    reset_token = secrets.token_urlsafe(32)
    reset_expiry = datetime.utcnow() + timedelta(hours=1)  # Token válido por 1 hora
    
    # Armazena token e data de expiração
    user.reset_password_token = reset_token
    user.reset_password_expires = reset_expiry
    db.commit()
    
    # URL para o frontend com o token
    reset_url = f"{recovery_data.frontend_url}?token={reset_token}"
    
    # Template HTML do e-mail
    html_content = f"""
    <html>
        <body>
            <h2>Recuperação de Senha</h2>
            <p>Olá {user.full_name},</p>
            <p>Recebemos uma solicitação para recuperar sua senha. Se você não fez esta solicitação, ignore este e-mail.</p>
            <p>Para criar uma nova senha, clique no link abaixo:</p>
            <p><a href="{reset_url}">Redefinir minha senha</a></p>
            <p>Este link é válido por 1 hora.</p>
            <p>Atenciosamente,<br>Equipe de Suporte</p>
        </body>
    </html>
    """
    
    # Envia e-mail com link de recuperação
    email_sent = send_email(
        user.email,
        "Recuperação de Senha",
        html_content
    )
    
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao enviar e-mail de recuperação"
        )
    
    logger.info(f"E-mail de recuperação enviado para: {user.email}")
    return {"message": "Se o e-mail estiver cadastrado, você receberá instruções para recuperar sua senha."}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Redefine a senha do usuário após validação do token
    """
    # Busca usuário pelo token
    user = db.query(User).filter(
        User.reset_password_token == reset_data.token
    ).first()
    
    # Verifica se o token existe e é válido
    if not user or not user.reset_password_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )
    
    # Verifica se o token expirou
    if datetime.utcnow() > user.reset_password_expires:
        # Limpa o token expirado
        user.reset_password_token = None
        user.reset_password_expires = None
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado. Solicite um novo link de recuperação."
        )
    
    # Verifica força da senha
    if len(reset_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha deve ter pelo menos 8 caracteres"
        )
    
    # Atualiza a senha
    user.hashed_password = User.get_password_hash(reset_data.new_password)
    
    # Limpa o token após o uso
    user.reset_password_token = None
    user.reset_password_expires = None
    
    # Salva as alterações
    db.commit()
    
    logger.info(f"Senha redefinida com sucesso para o usuário: {user.email}")
    return {"message": "Senha redefinida com sucesso"} 