"""
Configurações centralizadas do sistema.
"""

from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()


USAGE_LIMITS: Dict[str, int] = {
    "free": {
        "daily_limit": 10,
        "reset_hour": 23,
        "description": "Limite diário de avaliações gratuitas",
    },
    "premium": {
        "daily_limit": 3,
        "reset_hour": 23,
        "max_activations": 3,
        "description": "Limite diário de avaliações premium e máximo de ativações",
    },
}


ASSISTANTS = {
    "free": {
        "id": os.getenv("OPENAI_ASSISTANT_ID_FREE"),
        "name": "Avaliador de Prompts (Gratuito)",
        "description": "Assistente para avaliação básica de prompts",
    },
    "premium": {
        "id": os.getenv("OPENAI_ASSISTANT_ID_PREMIUM"),
        "name": "Avaliador de Prompts (Premium)",
        "description": "Assistente especializado para avaliação detalhada de prompts",
    },
}


MESSAGES = {
    "free_limit_reached": "Você atingiu o limite de {limit} avaliações gratuitas hoje. Tente novamente amanhã ou assine o plano premium.",
    "premium_limit_reached": "Você atingiu o limite de {limit} avaliações premium gratuitas. Assine o plano premium por $5/mês para uso ilimitado.",
}
