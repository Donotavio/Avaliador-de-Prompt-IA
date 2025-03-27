"""
Módulo para gerenciar a proteção CSRF (Cross-Site Request Forgery).
Implementa geração, validação e verificação de tokens CSRF.
"""

import secrets
import logging
import time
from typing import Dict, Optional, Tuple
from fastapi import Request, HTTPException, status, Depends, Cookie
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# Configuração de logging
logger = logging.getLogger(__name__)

# Constantes
CSRF_TOKEN_LENGTH = 32
CSRF_TOKEN_EXPIRY = 3600  # 1 hora em segundos
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_COOKIE_NAME = "csrf_token"

# Armazenamento em memória de tokens (em produção, usar Redis ou similar)
# Estrutura: {"token": {"user_id": "...", "expires_at": 12345}}
_csrf_tokens: Dict[str, Dict] = {}

def cleanup_expired_tokens() -> None:
    """Remove tokens expirados do armazenamento em memória"""
    current_time = time.time()
    tokens_to_remove = [
        token for token, data in _csrf_tokens.items() 
        if data["expires_at"] < current_time
    ]
    
    for token in tokens_to_remove:
        _csrf_tokens.pop(token, None)
    
    if tokens_to_remove:
        logger.info(f"Removidos {len(tokens_to_remove)} tokens CSRF expirados")

def generate_csrf_token(user_id: str) -> str:
    """
    Gera um novo token CSRF para o usuário especificado.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        str: Token CSRF gerado
    """
    # Limpa tokens expirados
    cleanup_expired_tokens()
    
    # Gera um novo token
    token = secrets.token_urlsafe(CSRF_TOKEN_LENGTH)
    expiry = time.time() + CSRF_TOKEN_EXPIRY
    
    # Armazena o token
    _csrf_tokens[token] = {
        "user_id": user_id,
        "expires_at": expiry
    }
    
    logger.debug(f"Gerado token CSRF para usuário {user_id}")
    return token

def validate_csrf_token(token: str, user_id: str) -> bool:
    """
    Valida um token CSRF para o usuário especificado.
    
    Args:
        token: Token CSRF a ser validado
        user_id: ID do usuário
        
    Returns:
        bool: True se o token for válido, False caso contrário
    """
    # Limpa tokens expirados
    cleanup_expired_tokens()
    
    # Verifica se o token existe
    if token not in _csrf_tokens:
        logger.warning(f"Token CSRF inválido: {token}")
        return False
    
    # Verifica se o token pertence ao usuário
    token_data = _csrf_tokens[token]
    if token_data["user_id"] != user_id:
        logger.warning(f"Token CSRF não pertence ao usuário {user_id}")
        return False
    
    # Verifica se o token está expirado
    if token_data["expires_at"] < time.time():
        logger.warning(f"Token CSRF expirado")
        _csrf_tokens.pop(token, None)
        return False
    
    return True

def set_csrf_token(response: Response, token: str) -> None:
    """
    Define o token CSRF em um cookie HTTP.
    
    Args:
        response: Resposta HTTP
        token: Token CSRF a ser definido
    """
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=CSRF_TOKEN_EXPIRY
    )

def verify_csrf_token(
    request: Request, 
    csrf_token: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
) -> bool:
    """
    Verifica se o token CSRF é válido para a requisição.
    
    Args:
        request: Requisição HTTP
        csrf_token: Token CSRF do cookie
        
    Returns:
        bool: True se o token for válido, False caso contrário
    """
    # Obtem o token do cabeçalho
    header_token = request.headers.get(CSRF_HEADER_NAME)
    
    # Verifica se ambos os tokens existem
    if not csrf_token or not header_token:
        return False
    
    # Verifica se os tokens são iguais
    if csrf_token != header_token:
        return False
    
    # Obtem o ID do usuário (se disponível)
    user_id = None
    if hasattr(request.state, "user") and request.state.user:
        user_id = request.state.user.id
    
    # Se não tiver usuário, aceita o token (para compatibilidade com rotas públicas)
    if not user_id:
        return True
    
    # Valida o token para o usuário
    return validate_csrf_token(csrf_token, user_id)

class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware para proteção CSRF.
    
    Verifica se as requisições POST, PUT e DELETE contêm um token CSRF válido.
    Gera um novo token CSRF para cada resposta de login.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Processa a requisição e aplica proteção CSRF.
        
        Args:
            request: Requisição HTTP
            call_next: Próxima função de middleware
        """
        # Métodos que não alteram estado não precisam de verificação
        safe_methods = {"GET", "HEAD", "OPTIONS"}
        
        # Rotas que estão isentas de verificação CSRF
        exempt_paths = {
            "/api/auth/login", 
            "/api/auth/register", 
            "/api/auth/forgot-password", 
            "/evaluate", 
            "/api/prompts/evaluate", 
            "/api/payments/create",
            "/api/contact",        # Formulário de contato
            "/api/health",         # Verificação de saúde da API
            "/api/auth/csrf-token", # Obtenção do token CSRF
            "/api/docs",            # Documentação da API
            "/api/redoc",           # Documentação alternativa
            "/api/openapi.json"     # Esquema OpenAPI
        }
        
        # Verifica se o path está isento de proteção CSRF
        path = request.url.path
        if any(path == exempt_path or path.startswith(exempt_path + "/") for exempt_path in exempt_paths):
            logger.info(f"Rota isenta de CSRF: {path}")
            # Importante: não verifica o token para rotas isentas
            return await call_next(request)
        
        # Métodos que não alteram estado não precisam de verificação
        if request.method in safe_methods:
            return await call_next(request)
            
        # Verifica o token CSRF para métodos que alteram estado e rotas não isentas
        if not verify_csrf_token(request):
            logger.warning(f"Tentativa de requisição sem token CSRF válido: {path}")
            return Response(
                content='{"detail":"Token CSRF inválido"}',
                status_code=status.HTTP_403_FORBIDDEN,
                media_type="application/json"
            )
        
        # Processa a requisição
        response = await call_next(request)
        
        # Para respostas de login bem-sucedidas, gera um novo token CSRF
        if (request.url.path == "/api/auth/login" and 
            request.method == "POST" and 
            response.status_code == status.HTTP_200_OK):
            
            # Obtem o ID do usuário (se disponível)
            user_id = None
            if hasattr(request.state, "user") and request.state.user:
                user_id = request.state.user.id
            else:
                # Usa um ID temporário
                user_id = f"temp_{secrets.token_hex(8)}"
            
            # Gera um novo token CSRF
            token = generate_csrf_token(user_id)
            set_csrf_token(response, token)
            logger.debug(f"Token CSRF gerado para login bem-sucedido")
        
        return response 