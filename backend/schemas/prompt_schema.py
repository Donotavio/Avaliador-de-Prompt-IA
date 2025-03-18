"""
Esquemas Pydantic para validação de dados relacionados a prompts.

Este módulo define os modelos de dados para entrada e saída da API
relacionados à avaliação e otimização de prompts.
"""

from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class PlanType(str, Enum):
    """Tipo de plano do usuário."""

    FREE = "free"
    PREMIUM = "premium"


class PromptBase(BaseModel):
    """
    Schema base para prompts.

    Attributes:
        content: Conteúdo do prompt
        context: Contexto adicional para o prompt
        plan_type: Tipo do plano (free ou premium)
        user_id: ID do usuário
        target_llm: Modelo LLM que o usuário está utilizando
    """

    content: str = Field(..., description="Conteúdo do prompt a ser avaliado")
    context: str = Field(
        None, description="Contexto adicional para ajudar na avaliação"
    )
    plan_type: PlanType = Field(
        default=PlanType.FREE, description="Tipo do plano (free ou premium)"
    )
    user_id: str = Field(None, description="ID do usuário")
    target_llm: str = Field(..., description="Modelo LLM que o usuário está utilizando")


class PromptEvaluation(BaseModel):
    """
    Schema para resultados da avaliação.

    Attributes:
        clarity_score: Pontuação de clareza
        context_score: Pontuação de contexto
        effectiveness_score: Pontuação de eficácia
        suggestions: Lista de sugestões de melhoria
        optimized_prompt: Versão otimizada do prompt
    """

    clarity_score: float = Field(
        ..., description="Pontuação de clareza (0-10)", ge=0, le=10
    )
    context_score: float = Field(
        ..., description="Pontuação de contexto (0-10)", ge=0, le=10
    )
    effectiveness_score: float = Field(
        ..., description="Pontuação de eficácia (0-10)", ge=0, le=10
    )
    suggestions: List[str] = Field(
        ..., description="Lista de sugestões para melhorar o prompt"
    )
    optimized_prompt: str = Field(..., description="Versão otimizada do prompt")


class PromptRequest(PromptBase):
    """Modelo para requisições de avaliação de prompt."""

    user_id: Optional[str] = Field(
        None, description="ID do usuário para controle de uso premium"
    )


class PromptResponse(BaseModel):
    """Modelo para respostas de avaliação de prompt."""

    original_prompt: PromptBase
    evaluation: PromptEvaluation
