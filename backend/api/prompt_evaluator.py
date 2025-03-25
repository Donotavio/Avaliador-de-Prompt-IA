"""
Rotas da API para avaliação de prompts.

Este módulo define os endpoints relacionados à avaliação e otimização
de prompts de IA.
"""

from fastapi import APIRouter, HTTPException
from core.evaluator import PromptEvaluator
from schemas.prompt_schema import PromptRequest, PromptResponse, PromptEvaluation

router = APIRouter(prefix="/prompts", tags=["prompts"])
evaluator = PromptEvaluator()


@router.post("/evaluate", response_model=PromptResponse)
async def evaluate_prompt(prompt: PromptRequest) -> PromptResponse:
    """
    Avalia um prompt de acordo com os critérios estabelecidos.

    Args:
        prompt: Objeto PromptRequest contendo o prompt a ser avaliado.

    Returns:
        PromptResponse: Resultado da avaliação do prompt.

    Raises:
        HTTPException: Se houver erro na avaliação do prompt.
    """
    try:
        # Compatibilidade com frontend - target_model -> target_llm
        if hasattr(prompt, 'target_model') and not hasattr(prompt, 'target_llm'):
            prompt.target_llm = prompt.target_model
        
        evaluation = await evaluator.evaluate(prompt)
        return PromptResponse(original_prompt=prompt, evaluation=evaluation)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao avaliar o prompt: {str(e)}"
        )
