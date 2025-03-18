"""
Módulo principal da aplicação FastAPI para avaliação de prompts de IA.

Este módulo configura e inicializa a aplicação FastAPI, definindo as rotas
principais e middleware necessários.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from api.prompt_evaluator import router as prompt_router
from core.evaluator import PromptEvaluator
from schemas.prompt_schema import (
    PromptBase,
    PromptEvaluation,
    PlanType,
    PromptRequest,
    PromptResponse,
)
from services.usage_manager import usage_manager
from utils.logger import logger

app = FastAPI(
    title="Avaliador de Prompts IA",
    description="API para avaliação e otimização de prompts para Inteligência Artificial",
    version="1.0.0",
)

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluindo os routers
app.include_router(prompt_router)

# Inicializa o avaliador
evaluator = PromptEvaluator()


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

        # Valida o prompt
        if len(request.content.strip()) < 10:
            logger.warn("Prompt muito curto")
            raise HTTPException(
                status_code=400, detail="O prompt deve ter pelo menos 10 caracteres"
            )

        # Avalia o prompt
        evaluation = await evaluator.evaluate(request)
        logger.info("Avaliação concluída com sucesso")

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


@app.post("/premium/activate/{user_id}")
async def activate_premium(user_id: str):
    """
    Ativa o plano premium para um usuário.

    Args:
        user_id: ID do usuário

    Returns:
        dict: Mensagem de sucesso
    """
    try:
        logger.info(f"Ativando plano premium para usuário: {user_id}")
        usage_manager.activate_premium(user_id)
        logger.info("Plano premium ativado com sucesso")
        return {"message": "Plano premium ativado com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao ativar plano premium: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/premium/status/{user_id}")
def check_premium_status(user_id: str):
    """
    Verifica o status do plano premium do usuário.

    Args:
        user_id: ID do usuário

    Returns:
        dict: Status do usuário incluindo se pode usar, mensagem e se expirou
    """
    try:
        logger.info(f"Verificando status premium do usuário: {user_id}")
        can_use, message, has_expired = usage_manager.can_use_premium(user_id)
        logger.info(f"Status premium verificado: {can_use}")
        return {"can_use": can_use, "message": message, "has_expired": has_expired}
    except Exception as e:
        logger.error(f"Erro ao verificar status premium: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao verificar status premium")


@app.get("/free/status/{user_id}")
async def check_free_status(user_id: str):
    """
    Verifica o status gratuito de um usuário.

    Args:
        user_id: ID do usuário

    Returns:
        dict: Status do usuário
    """
    try:
        logger.info(f"Verificando status gratuito do usuário: {user_id}")
        can_use, message = usage_manager.can_use_free(user_id)
        logger.info(f"Status gratuito verificado: {can_use}")
        return {"can_use_free": can_use, "message": message}
    except Exception as e:
        logger.error(f"Erro ao verificar status gratuito: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset/{user_id}")
async def reset_usage(user_id: str):
    """
    Reseta o uso premium de um usuário.

    Args:
        user_id: ID do usuário

    Returns:
        dict: Mensagem de sucesso
    """
    try:
        logger.info(f"Resetando uso do usuário: {user_id}")
        usage_manager.reset_premium_usage(user_id)
        logger.info("Uso resetado com sucesso")
        return {"message": "Uso resetado com sucesso"}
    except Exception as e:
        logger.error(f"Erro ao resetar uso: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    logger.info("Iniciando servidor da API")
    uvicorn.run(app, host="0.0.0.0", port=8000)
