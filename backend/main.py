"""
Módulo principal da aplicação FastAPI para avaliação de prompts de IA.

Este módulo configura e inicializa a aplicação FastAPI, definindo as rotas
principais e middleware necessários.
"""

# Importa o patch para OpenAI antes de qualquer outra coisa
import services.openai_patch as openai_patch

from fastapi import FastAPI, HTTPException, Request, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from api.prompt_evaluator import router as prompt_router
from api.routes import router as routes_router
from core.evaluator import PromptEvaluator
from schemas.prompt_schema import (
    PromptRequest,
    PromptResponse,
)
from services.usage_manager import usage_manager
from utils.logger import logger
from config.settings import USAGE_LIMITS

# Importação para sistema de usuários e pagamentos
from services.database import Base, engine, get_db
from api import auth, users, payments, products
from models.user import User
from services.auth import get_current_user, get_current_admin_user
from sqlalchemy.orm import Session
from typing import Optional
from fastapi.security import OAuth2PasswordBearer
import uvicorn
import os
import secrets

from services.token_security import initialize_jwt_keys
# Importação para proteção CSRF
from services.csrf_protection import CSRFProtectionMiddleware, generate_csrf_token, set_csrf_token

# Constantes para configuração da API
API_PREFIX = "/api"
# Definindo origens permitidas de forma segura
ALLOWED_HOSTS = [
    "https://avaliadorprompt.com.br",  # Domínio principal em produção
    "https://www.avaliadorprompt.com.br",  # Subdomínio www em produção
    "http://localhost:3000",  # Ambiente de desenvolvimento local frontend
    "http://localhost:5000",   # Ambiente de teste local
    "http://localhost:8000"    # Ambiente de desenvolvimento local API
]

# Permitir todos os hosts em desenvolvimento
if os.getenv("ENV") != "production":
    # Em desenvolvimento, permitimos todas as origens para facilitar testes
    ALLOWED_HOSTS = ["*"]

# Cria tabelas no banco de dados (se não existirem)
# Nota: Para migrações complexas, use o Alembic: 
# `alembic upgrade head`
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Avaliador de Prompts IA",
    description="API para avaliação e otimização de prompts para Inteligência Artificial",
    version="1.0.0",
    openapi_url=f"{API_PREFIX}/openapi.json",
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
)

# Adiciona middleware de segurança para cabeçalhos adicionais
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Middleware para adicionar cabeçalhos de segurança a todas as respostas.
    Ajuda a mitigar vulnerabilidades XSS, clickjacking e outros tipos de ataques.
    """
    response = await call_next(request)
    
    # Previne clickjacking (a página só pode ser exibida no mesmo domínio)
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    
    # Previne XSS forçando o navegador a cumprir o tipo de conteúdo declarado
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Ativa a proteção XSS em navegadores antigos
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Força conexões HTTPS
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Define política de recursos - política CSP básica que pode ser expandida conforme necessário
    csp_directives = [
        "default-src 'self'",
        "img-src 'self' data: https://cdn.avaliadorprompt.com.br",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "script-src 'self' 'unsafe-inline' https://cdn.avaliadorprompt.com.br",
        "connect-src 'self'" + ''.join(f" {host}" for host in ALLOWED_HOSTS)
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
    
    # Define política de referrer
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Incluindo OPTIONS para pre-flight requests
    allow_headers=["*"],  # Permite todos os cabeçalhos em desenvolvimento
)

# Adiciona middleware de proteção CSRF
if os.getenv("ENV") == "production":
    app.add_middleware(CSRFProtectionMiddleware)
else:
    logger.warning("Proteção CSRF desabilitada em ambiente de desenvolvimento")

# Inclui rotas com prefixo API
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(payments.router, prefix="/api", tags=["payments"])
app.include_router(products.router, prefix="/api", tags=["products"])
app.include_router(prompt_router, prefix="/api", tags=["prompt_evaluator"])
app.include_router(routes_router, prefix="/api", tags=["routes"])

# Inicializa o avaliador
evaluator = PromptEvaluator()

# Adiciona endpoint para obter token CSRF
@app.get(f"{API_PREFIX}/csrf-token")
async def get_csrf_token(response: Response, request: Request):
    """
    Gera um novo token CSRF acessível por rota pública.
    """
    # Usa um ID temporário para usuários não autenticados
    user_id = f"temp_{secrets.token_hex(8)}"
    
    # Gera um novo token CSRF
    csrf_token = generate_csrf_token(user_id)
    
    # Define o token no cookie
    set_csrf_token(response, csrf_token)
    
    # Log para depuração
    logger.info(f"Token CSRF gerado: {csrf_token}")
    
    # Retorna o token na resposta
    return {"csrf_token": csrf_token}

# OAuth2 schema opcional que não levanta exceção se não houver token
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f"{API_PREFIX}/auth/login",
    auto_error=False
)

# Função para obter o usuário atual (opcional)
def get_current_user_optional(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme_optional)
) -> Optional[User]:
    """
    Obtém o usuário atual se autenticado, ou None se não autenticado.
    """
    if not token:
        return None
    
    try:
        return get_current_user(db=db, token=token)
    except:
        return None

# Cria rotas espelho da API para manter compatibilidade
@app.get(f"{API_PREFIX}/free/status/{{user_id}}")
async def api_check_free_status(
    user_id: str,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Versão da API da função check_free_status.
    Mantida para compatibilidade com o frontend.
    """
    logger.info(f"API prefix endpoint acessado para verificação de status gratuito")
    # Garantir que esta função espelhe exatamente a lógica de check_free_status
    return await check_free_status(user_id, request, current_user)

@app.get("/")
async def root():
    """Endpoint raiz para verificar se a API está funcionando."""
    logger.info("Endpoint raiz acessado")
    return {"message": "API de Avaliação de Prompts"}

@app.post("/evaluate", response_model=PromptResponse)
async def evaluate_prompt(request: PromptRequest):
    """
    Avalia um prompt usando o plano especificado.

    Args:
        request: PromptRequest contendo o prompt e metadados

    Returns:
        PromptResponse: Resultado da avaliação
    """
    try:
        logger.info(f"Iniciando avaliação de prompt - Plano: {request.plan_type}")
        logger.debug(f"Dados da requisição: {request.dict()}")

        # Valida o prompt
        if len(request.content.strip()) < 10:
            logger.warn("Prompt muito curto")
            raise HTTPException(
                status_code=400, detail="O prompt deve ter pelo menos 10 caracteres"
            )
            
        # Compatibilidade com frontend - target_model -> target_llm
        if hasattr(request, 'target_model') and not hasattr(request, 'target_llm'):
            request.target_llm = request.target_model
            logger.debug(f"Convertido target_model para target_llm: {request.target_llm}")

        # Avalia o prompt
        try:
            evaluation = await evaluator.evaluate(request)
            logger.info("Avaliação concluída com sucesso")
        except Exception as eval_error:
            logger.error(f"Erro na avaliação: {str(eval_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao processar avaliação: {str(eval_error)}"
            )

        # Log do resultado para debug
        response = PromptResponse(
            original_prompt=request,
            evaluation=evaluation
        )
        logger.info(f"Resultado enviado ao frontend: {evaluation.dict()}")

        return response

    except ValueError as e:
        logger.error(f"Erro de validação: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro interno: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao avaliar prompt")

@app.get("/premium/status/{user_id}")
async def check_premium_status(
    user_id: str,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Verifica o status do plano premium de um usuário.
    Permite acesso anônimo para o ID 'anon'.

    Args:
        user_id: ID do usuário
        request: Requisição HTTP
        current_user: Usuário autenticado (opcional)

    Returns:
        dict: Status do plano premium
    """
    # Para usuários anônimos, permitir apenas verificar 'anon'
    if user_id == "anon":
        # Para anônimos, sempre retorna que não tem premium, mas pode assinar
        logger.info("Verificando status premium para usuário anônimo")
        return {
            "can_use": False, 
            "message": "Usuário não autenticado", 
            "has_expired": False
        }
    
    # Para usuários autenticados, verificar permissões
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Autenticação necessária para verificar status premium de usuário específico"
        )
        
    # Garantir que o usuário só pode verificar seu próprio status (ou é admin)
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=403, 
            detail="Você só pode verificar seu próprio status premium"
        )
        
    try:
        logger.info(f"Verificando status premium do usuário: {user_id}")
        can_use, message, has_expired = usage_manager.can_use_premium(user_id)
        logger.info(f"Status premium: {can_use}, Mensagem: {message}")
        
        # Se o usuário pode usar premium, não retornar mensagem de status
        if can_use and message == "Uso ilimitado (Plano Premium)":
            return {
                "status": can_use,
                "has_expired": has_expired,
                "evaluation_count": usage_manager.get_user_usage(user_id).premium_evaluations_count
            }
        
        return {
            "status": can_use, 
            "message": message, 
            "has_expired": has_expired,
            "evaluation_count": usage_manager.get_user_usage(user_id).premium_evaluations_count
        }
    except Exception as e:
        logger.error(f"Erro ao verificar status premium: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/free/status/{user_id}")
async def check_free_status(
    user_id: str,
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Verifica o status do plano gratuito de um usuário.
    Permite acesso anônimo para o ID 'anon'.

    Args:
        user_id: ID do usuário
        request: Requisição HTTP
        current_user: Usuário autenticado (opcional)

    Returns:
        dict: Status do plano gratuito
    """
    # Se o usuário está autenticado, usar seu ID real
    if current_user:
        user_id_to_check = current_user.id
        logger.info(f"Usuário autenticado: {user_id_to_check}, verificando status gratuito")
    # Para usuários anônimos ou se for explicitamente solicitado o status anônimo
    elif user_id == "anon":
        # Para usuários anônimos, verificamos pelo IP
        client_ip = request.client.host
        user_id_to_check = f"anon_{client_ip}"
        logger.info(f"Verificando status gratuito para usuário anônimo: {user_id_to_check}")
    else:
        # Se não for anônimo nem autenticado, usar o ID fornecido
        user_id_to_check = user_id
        logger.info(f"Verificando status gratuito para usuário específico: {user_id_to_check}")
    
    # Verificar se o usuário pode usar o plano gratuito
    can_use_free, message = usage_manager.can_use_free(user_id_to_check)
    logger.info(f"Status gratuito para {user_id_to_check}: {can_use_free}, Mensagem: {message}")
    
    # Se for usuário anônimo e for o primeiro uso, retornar sempre true
    if user_id_to_check.startswith("anon_") and not can_use_free and "já utilizou" in message:
        message = "Primeira avaliação gratuita"
        can_use_free = True
        
    return {
        "can_use_free": can_use_free, 
        "status": can_use_free,  # Para compatibilidade
        "message": message
    }


@app.post("/reset/{user_id}")
async def reset_usage(
    user_id: str, 
    current_user: User = Depends(get_current_admin_user)
):
    """
    Reseta o uso premium de um usuário.
    Requer privilégios de administrador.

    Args:
        user_id: ID do usuário
        current_user: Usuário administrador autenticado

    Returns:
        dict: Mensagem de sucesso
    """
    try:
        logger.info(f"Admin {current_user.id} resetando uso do usuário: {user_id}")
        usage_manager.reset_premium_usage(user_id)
        logger.info("Uso resetado com sucesso")
        return {"message": "Uso resetado com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao resetar uso: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/create-default-user")
async def create_default_user(db: Session = Depends(get_db)):
    """
    Cria o usuário padrão (user123) se ele ainda não existir no sistema
    Usado apenas para desenvolvimento e testes
    """
    try:
        # Verifica se o usuário já existe no banco
        default_user_id = "user123"
        db_user = db.query(User).filter(User.id == default_user_id).first()
        
        if db_user:
            return {"message": "Usuário padrão já existe", "user_id": db_user.id}
        
        # Cria o usuário padrão com um UUID específico
        import uuid
        default_user = User(
            id=default_user_id,
            email="default@example.com",
            full_name="Usuário Padrão",
            hashed_password=User.get_password_hash("password123"),
            is_active=True
        )
        
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
        
        # Ativa o premium para este usuário
        usage_manager.activate_premium(default_user_id)
        
        logger.info(f"Usuário padrão criado com ID: {default_user_id}")
        return {"message": "Usuário padrão criado com sucesso", "user_id": default_user_id}
    except Exception as e:
        logger.error(f"Erro ao criar usuário padrão: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar usuário padrão: {str(e)}")


@app.post("/admin/reset-premium-usage/{user_id}")
async def admin_reset_premium_usage(user_id: str):
    """
    Reseta completamente o uso premium de um usuário, incluindo o contador de ativações
    Endpoint administrativo para resolver problemas e testes
    """
    try:
        logger.info(f"[ADMIN] Resetando completamente uso premium do usuário: {user_id}")
        
        # Obtém o usuário do gerenciador
        if user_id in usage_manager.user_usage:
            # Reseta todos os contadores relevantes
            usage_manager.user_usage[user_id].premium_evaluations_count = 0
            usage_manager.user_usage[user_id].premium_activations_count = 0
            usage_manager.user_usage[user_id].is_premium_active = False
            
            # Salva as alterações
            usage_manager._save_data()
            logger.info(f"[ADMIN] Uso premium completamente resetado para usuário {user_id}")
            return {"message": "Uso premium completamente resetado com sucesso"}
        else:
            logger.warning(f"[ADMIN] Usuário {user_id} não encontrado para reset")
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
    except Exception as e:
        logger.error(f"[ADMIN] Erro ao resetar uso premium: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao resetar uso premium: {str(e)}")

@app.get(f"{API_PREFIX}/health")
async def health_check():
    """
    Endpoint simples para verificar se a API está funcionando.
    Usado para monitoramento e diagnóstico.
    """
    return {"status": "ok", "message": "API está funcionando corretamente"}

# Initialize JWT keys at startup
initialize_jwt_keys()

if __name__ == "__main__":
    logger.info("Iniciando servidor da API")
    uvicorn.run(app, host="0.0.0.0", port=8000)
