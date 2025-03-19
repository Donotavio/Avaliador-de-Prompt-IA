from fastapi import APIRouter
from services.usage_manager import usage_manager
from config.settings import USAGE_LIMITS

router = APIRouter()

@router.get("/free/status/{user_id}")
async def get_free_status(user_id: str):
    """
    Verifica o status do usuário para avaliações gratuitas
    
    Returns:
        - Dict com status, limite e mensagem
    """
    user_usage = usage_manager.get_user_usage(user_id)
    can_use, message = user_usage.can_use_free()
    
    # Não incluir a mensagem na resposta se o usuário pode usar normalmente
    if can_use and not message:
        return {
            "status": can_use,
            "evaluation_count": user_usage.free_evaluations_count,
            "daily_limit": USAGE_LIMITS["free"]["daily_limit"]
        }
    
    return {
        "status": can_use,
        "message": message,
        "evaluation_count": user_usage.free_evaluations_count,
        "daily_limit": USAGE_LIMITS["free"]["daily_limit"]
    } 