"""
Esquemas Pydantic para validação de dados relacionados a prompts.

Este módulo define os modelos de dados para entrada e saída da API
relacionados à avaliação e otimização de prompts.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class PlanType(str, Enum):
    """Tipo de plano do usuário."""

    FREE = "free"
    PREMIUM = "premium"


class DetailedAnalysis(BaseModel):
    """
    Schema para análise detalhada do prompt.
    
    Attributes:
        central_objective: Objetivo central identificado no prompt
        strengths_weaknesses: Pontos fortes e fracos da redação original
        context: Avaliação se o prompt oferece contexto suficiente e estruturado
        practical_suggestions: Explicação detalhada sobre as sugestões práticas
        ethical_practices: Avaliação da aderência às melhores práticas éticas
    """
    
    central_objective: str = Field(..., description="Objetivo central identificado no prompt")
    strengths_weaknesses: str = Field(..., description="Pontos fortes e fracos da redação original")
    context: str = Field(..., description="Avaliação se o prompt oferece contexto suficiente e estruturado")
    practical_suggestions: str = Field(..., description="Explicação detalhada sobre as sugestões práticas fornecidas")
    ethical_practices: str = Field(..., description="Avaliação da aderência às melhores práticas éticas em interação com IA")


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
        detailed_analysis: Análise detalhada do prompt
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
    detailed_analysis: Optional[DetailedAnalysis] = Field(
        None, description="Análise detalhada do prompt, incluindo objetivo central, pontos fortes e fracos, contexto, sugestões práticas e práticas éticas"
    )


class PromptRequest(PromptBase):
    """Modelo para requisições de avaliação de prompt."""

    user_id: Optional[str] = Field(
        None, description="ID do usuário para controle de uso premium"
    )


class PromptResponse(BaseModel):
    """Modelo para respostas de avaliação de prompt."""

    original_prompt: PromptBase
    evaluation: PromptEvaluation
