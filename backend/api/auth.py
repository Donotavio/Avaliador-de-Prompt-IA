from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from typing import Any, Dict, Optional
import logging
import re
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import jwt
from passlib.context import CryptContext
import random
import string

from services.database import get_db
from models.user import User
from schemas.user_schema import UserCreate, User as UserSchema, PasswordRecovery, PasswordReset, EmailVerification, ResendVerification
from schemas.token_schema import Token, RefreshRequest
from services.auth import (
    authenticate_user, 
    get_current_user, 
    create_tokens_for_user, 
    get_client_ip,
    decode_token,
    create_access_token,
    oauth2_scheme
)
from services.token_security import JWT_ACCESS_TOKEN_EXPIRE_MINUTES
from services.abacate_pay import AbacatePayClient
from utils.email_security import sanitize_html, create_safe_email_template, sanitize_recovery_link
from services.csrf_protection import generate_csrf_token, set_csrf_token

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

# Configuração para hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

def generate_verification_token() -> str:
    """
    Gera um token numérico de 6 dígitos para verificação de e-mail
    """
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(user: User, db: Session) -> bool:
    """
    Gera um token de verificação e envia email para o usuário
    """
    # Gera um token de verificação
    token = generate_verification_token()
    
    # Define o tempo de expiração (15 minutos)
    expiration = datetime.now() + timedelta(minutes=15)
    
    # Atualiza o usuário com o token
    user.email_verification_token = token
    user.email_token_expires = expiration
    db.commit()
    
    # Cria o template do e-mail
    subject = "Verificação de Conta"
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #4a56e2; color: white; padding: 10px 20px; text-align: center;">
                <h2>Verificação de Conta</h2>
            </div>
            <div style="padding: 20px; background-color: #f9f9f9; border: 1px solid #ddd;">
                <p>Olá {user.full_name},</p>
                <p>Obrigado por se cadastrar! Para verificar sua conta, utilize o código abaixo:</p>
                <div style="font-size: 24px; font-weight: bold; text-align: center; margin: 20px 0; padding: 10px; background-color: #eee;">{token}</div>
                <p>Este código é válido por 15 minutos.</p>
                <p>Se você não solicitou este código, por favor ignore este e-mail.</p>
            </div>
            <div style="font-size: 12px; text-align: center; margin-top: 20px; color: #666;">
                <p>Esta é uma mensagem automática, por favor não responda.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Envia o e-mail
    return send_email(user.email, subject, html_content)

def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Envia um e-mail com o conteúdo especificado
    """
    if not EMAIL_USER or not EMAIL_PASSWORD:
        logger.error("Configurações de e-mail não definidas")
        return False
    
    try:
        # Sanitiza o conteúdo HTML para evitar XSS
        safe_html = sanitize_html(html_content)
        
        message = MIMEMultipart()
        message["From"] = EMAIL_FROM
        message["To"] = to_email
        message["Subject"] = subject
        
        # Adiciona o corpo HTML sanitizado
        message.attach(MIMEText(safe_html, "html"))
        
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
        "is_admin": current_user.is_admin,
        "is_email_verified": current_user.is_email_verified
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
            hashed_password=User.get_password_hash(user_data.password),
            is_email_verified=False
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"Usuário registrado com sucesso: {user_data.email}")
        
        # Envia e-mail de verificação
        send_verification_email(new_user, db)
        
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
            detail="Erro no banco de dados. Por favor, tente novamente mais tarde."
        )
    except Exception as e:
        logger.error(f"Erro ao registrar usuário: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/verify-email", status_code=status.HTTP_200_OK)
def verify_email(verification: EmailVerification, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Verifica o e-mail de um usuário com o token enviado
    """
    try:
        # Busca o usuário pelo ID
        user = db.query(User).filter(User.id == verification.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Verifica se o e-mail já foi verificado
        if user.is_email_verified:
            return {"message": "E-mail já foi verificado"}
        
        # Verifica se o token é válido
        if not user.email_verification_token or user.email_verification_token != verification.token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de verificação inválido"
            )
        
        # Verifica se o token expirou
        if user.email_token_expires and user.email_token_expires < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de verificação expirado"
            )
        
        # Atualiza o usuário como verificado
        user.is_email_verified = True
        user.email_verification_token = None
        user.email_token_expires = None
        db.commit()
        
        # Gera tokens para login automático
        tokens = create_tokens_for_user(user)
        
        # Retorna tokens de autenticação para login automático
        return {
            "message": "E-mail verificado com sucesso",
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao verificar e-mail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao verificar e-mail. Por favor, tente novamente mais tarde."
        )

@router.post("/resend-verification", status_code=status.HTTP_200_OK)
def resend_verification(resend: ResendVerification, db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Reenvia o token de verificação para o e-mail do usuário
    """
    try:
        # Busca o usuário pelo ID
        user = db.query(User).filter(User.id == resend.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        # Verifica se o e-mail já foi verificado
        if user.is_email_verified:
            return {"message": "E-mail já foi verificado"}
        
        # Verifica limite de tempo para reenvio (1 minuto entre solicitações)
        if user.email_token_expires and user.email_token_expires > datetime.now() - timedelta(minutes=14):
            time_left = int((user.email_token_expires - (datetime.now() - timedelta(minutes=14))).total_seconds())
            if time_left > 0:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Aguarde {time_left} segundos antes de solicitar um novo código"
                )
        
        # Envia um novo e-mail de verificação
        if send_verification_email(user, db):
            return {"message": "E-mail de verificação reenviado com sucesso"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao enviar e-mail de verificação"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao reenviar verificação: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao reenviar verificação. Por favor, tente novamente mais tarde."
        )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db), request: Request = None, response: Response = None):
    """
    Gera um token de acesso JWT para o usuário
    """
    try:
        # Obtem o IP do cliente para rastreamento
        client_ip = get_client_ip(request)
        logger.info(f"Tentativa de login de IP: {client_ip}")
        
        # Autentica o usuário
        user = authenticate_user(db=db, email=form_data.username, password=form_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Gera tokens de acesso e atualização
        tokens = create_tokens_for_user(user)
        
        # Registra o token em user.active_tokens
        if not user.active_tokens:
            user.active_tokens = []
            
        # Adiciona o novo token à lista (com timestamp)
        user.active_tokens.append({
            "token_id": str(user.id),
            "created_at": datetime.timestamp(datetime.utcnow()),
            "user_agent": request.headers.get("user-agent", "unknown") if request else "unknown",
            "ip_address": client_ip
        })
        
        # Limita a 5 sessões ativas
        if len(user.active_tokens) > 5:
            user.active_tokens = user.active_tokens[-5:]
            
        db.commit()
        
        # Gera token CSRF para o usuário
        csrf_token = generate_csrf_token(str(user.id))
        
        # Define o token CSRF no cookie
        if response:
            set_csrf_token(response, csrf_token)
        
        # Retorna os tokens de acesso e atualização junto com o token CSRF
        tokens_dict = tokens.dict()
        return {
            **tokens_dict,
            "csrf_token": csrf_token  # Inclui o token CSRF na resposta
        }
        
    except Exception as e:
        logger.error(f"Erro ao realizar login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar login"
        )

@router.get("/csrf-token")
async def get_csrf_token(response: Response, request: Request):
    """
    Gera um novo token CSRF.
    O token é retornado na resposta e também definido em um cookie.
    
    Returns:
        dict: Contendo o token CSRF
    """
    # Tenta obter o usuário atual se autenticado
    user_id = None
    try:
        token = request.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token.replace("Bearer ", "")
            # Decode the token to get the user_id
            payload = decode_token(token)
            user_id = payload.get("sub")
    except Exception as e:
        # Se não conseguir obter o usuário, usa um ID temporário
        pass
    
    # Se não tiver usuário, usa um ID temporário
    if not user_id:
        user_id = f"temp_{secrets.token_hex(8)}"
    
    # Gera um novo token CSRF para o usuário
    csrf_token = generate_csrf_token(user_id)
    
    # Define o token no cookie
    set_csrf_token(response, csrf_token)
    
    # Retorna o token na resposta
    return {"csrf_token": csrf_token}

@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_request: RefreshRequest,
    db: Session = Depends(get_db),
    request: Request = None
) -> Dict[str, Any]:
    """
    Renova o token de acesso usando um refresh token
    """
    try:
        # Decodifica o refresh token
        payload = decode_token(refresh_request.refresh_token)
        
        # Verifica se é um token de refresh
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido para refresh",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Busca o usuário
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário inválido ou inativo",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Gera novos tokens
        tokens = create_tokens_for_user(user)
        
        # Atualiza informações de sessão
        if not user.active_tokens:
            user.active_tokens = []
        
        # Adiciona informações sobre a nova sessão
        client_ip = get_client_ip(request) if request else "unknown"
        now = datetime.utcnow()
        
        token_info = {
            "token_id": secrets.token_hex(8),
            "refreshed_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat(),
            "ip": client_ip,
            "user_agent": request.headers.get("User-Agent", "Unknown") if request else "Unknown"
        }
        
        user.active_tokens.append(token_info)
        
        # Manter no máximo 5 tokens ativos por usuário
        if len(user.active_tokens) > 5:
            user.active_tokens = user.active_tokens[-5:]
        
        db.commit()
        
        return tokens
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar refresh de token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falha ao renovar o token",
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Realiza logout, invalidando o token atual
    """
    try:
        # Decodifica o token para obter seu ID (sem validar)
        header = jwt.get_unverified_header(token)
        kid = header.get("kid", "unknown")
        
        # Remove o token da lista de tokens ativos
        if current_user.active_tokens:
            current_user.active_tokens = [
                t for t in current_user.active_tokens 
                if t.get("token_id") != kid
            ]
            db.commit()
        
        return {"message": "Logout realizado com sucesso"}
    
    except Exception as e:
        logger.error(f"Erro ao processar logout: {str(e)}")
        # Mesmo com erro, indicamos sucesso para o cliente
        return {"message": "Logout realizado com sucesso"}

@router.post("/logout-all")
def logout_all(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Realiza logout de todas as sessões do usuário
    """
    try:
        # Limpa todos os tokens ativos
        current_user.active_tokens = []
        db.commit()
        
        return {"message": "Todas as sessões foram encerradas com sucesso"}
    
    except Exception as e:
        logger.error(f"Erro ao processar logout de todas as sessões: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar a requisição"
        )

@router.get("/sessions")
def list_active_sessions(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Lista todas as sessões ativas do usuário
    """
    sessions = []
    
    if current_user.active_tokens:
        for token in current_user.active_tokens:
            session = {
                "session_id": token.get("token_id", "unknown"),
                "started_at": token.get("issued_at") or token.get("refreshed_at", "unknown"),
                "expires_at": token.get("expires_at", "unknown"),
                "ip": token.get("ip", "unknown"),
                "user_agent": token.get("user_agent", "unknown")
            }
            sessions.append(session)
    
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "active_sessions": sessions
    }

@router.delete("/sessions/{session_id}")
def terminate_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Encerra uma sessão específica do usuário
    """
    if not current_user.active_tokens:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada"
        )
    
    # Procura e remove a sessão específica
    original_count = len(current_user.active_tokens)
    current_user.active_tokens = [
        t for t in current_user.active_tokens 
        if t.get("token_id") != session_id
    ]
    
    # Verifica se algo foi removido
    if len(current_user.active_tokens) == original_count:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada"
        )
    
    db.commit()
    
    return {"message": "Sessão encerrada com sucesso"}

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(recover: PasswordRecovery, db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Envia e-mail de recuperação de senha
    """
    try:
        # Log das variáveis de ambiente de email para debug
        logger.info(f"DEBUG - Configurações de email: HOST={EMAIL_HOST}, PORT={EMAIL_PORT}, USER={EMAIL_USER}, FROM={EMAIL_FROM}")
        
        # Busca usuário pelo e-mail
        user = db.query(User).filter(User.email == recover.email).first()
        
        if not user:
            # Não revela se o e-mail existe (proteção contra enumeração)
            logger.warning(f"Tentativa de recuperação para e-mail não cadastrado: {recover.email}")
            return {"message": "Se o e-mail estiver cadastrado, você receberá as instruções de recuperação."}
            
        # Gera token aleatório
        reset_token = secrets.token_urlsafe(32)
        expiration = datetime.utcnow() + timedelta(hours=1)
        
        # Salva token no banco
        user.reset_password_token = reset_token
        user.reset_password_expires = expiration
        db.commit()
        
        # Prepara variáveis para e-mail
        sender_email = EMAIL_USER
        receiver_email = user.email
        
        # Cria link de recuperação e sanitiza
        base_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        recovery_link_raw = f"{base_url}/reset-password?token={reset_token}"
        recovery_link = sanitize_recovery_link(recovery_link_raw)
        
        if not recovery_link:
            logger.error(f"Link de recuperação inválido: {recovery_link_raw}")
            recovery_link = "#"  # Link vazio em caso de falha na sanitização
        
        # Conteúdo HTML
        title = "Recuperação de Senha"
        header = f"Olá {sanitize_html(user.full_name)},"
        main_content = f"""
        <p>Você solicitou a recuperação de senha para sua conta no Prompt AI Evaluator.</p>
        <p>Clique no link abaixo para definir uma nova senha:</p>
        <p><a href="{recovery_link}">Recuperar senha</a></p>
        <p>Este link é válido por 1 hora.</p>
        <p>Se você não solicitou esta recuperação, ignore este e-mail.</p>
        """
        
        # Cria template de e-mail seguro
        html = create_safe_email_template(title, header, main_content)
        
        try:
            # Cria mensagem
            message = MIMEMultipart("alternative")
            message["Subject"] = "Recuperação de Senha - Prompt AI Evaluator"
            message["From"] = sender_email
            message["To"] = receiver_email
            
            # Log para debug
            logger.info(f"DEBUG - Enviando email para: {receiver_email}, Usando remetente: {sender_email}")
            
            # Adiciona partes à mensagem
            message.attach(MIMEText(html, "html"))
            
            # Configura servidor SMTP
            logger.info(f"DEBUG - Conectando ao servidor SMTP: {EMAIL_HOST}:{EMAIL_PORT}")
            if EMAIL_PORT == 465:
                # Usar conexão SSL direta para porta 465
                server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
                logger.info("DEBUG - Usando conexão SSL")
            else:
                # Usar TLS para outras portas (como 587)
                server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
                server.starttls()
                logger.info("DEBUG - Usando conexão TLS")
            
            # Envia e-mail
            logger.info("DEBUG - Autenticando no servidor SMTP")
            server.login(sender_email, EMAIL_PASSWORD)
            logger.info("DEBUG - Enviando email")
            server.sendmail(sender_email, receiver_email, message.as_string())
            server.quit()
            logger.info(f"E-mail de recuperação enviado para: {recover.email}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail de recuperação: {str(e)}")
            # Registra stack trace completo para debug
            import traceback
            logger.error(f"Stack trace completo: {traceback.format_exc()}")
            # Não revelar erro específico ao usuário
        
        return {"message": "Se o e-mail estiver cadastrado, você receberá as instruções de recuperação."}
        
    except OperationalError as e:
        logger.error(f"Erro de banco ao processar recuperação de senha: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço temporariamente indisponível. Tente novamente em alguns instantes."
        )
    except Exception as e:
        logger.error(f"Erro inesperado na recuperação de senha: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar a solicitação."
        )

def get_password_hash(password: str) -> str:
    """Gera um hash da senha"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Erro crítico ao gerar hash de senha: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro crítico no sistema de segurança. Por favor, entre em contato com o suporte."
        )

@router.post("/reset-password", status_code=status.HTTP_200_OK, response_model=Token)
def reset_password(reset: PasswordReset, db: Session = Depends(get_db)) -> Token:
    """
    Redefine a senha com o token de recuperação
    """
    try:
        now = datetime.utcnow()
        
        # Verifica token e expiração
        user = db.query(User).filter(
            User.reset_password_token == reset.token,
            User.reset_password_expires > now
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido ou expirado."
            )
            
        # Atualiza a senha
        hashed_password = get_password_hash(reset.new_password)
        user.hashed_password = hashed_password
        
        # Limpa o token de recuperação
        user.reset_password_token = None
        user.reset_password_expires = None
        
        # Registra último login para o usuário
        user.last_login = now
        
        db.commit()
        logger.info(f"Senha redefinida com sucesso para o usuário: {user.email}")
        
        # Gera token de acesso após redefinição bem sucedida
        tokens = create_tokens_for_user(user)
        
        return tokens
        
    except HTTPException:
        raise
    except OperationalError as e:
        logger.error(f"Erro de banco ao redefinir senha: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço temporariamente indisponível. Tente novamente em alguns instantes."
        )
    except Exception as e:
        logger.error(f"Erro inesperado na redefinição de senha: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar a solicitação."
        ) 