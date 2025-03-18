"""
Módulo principal para avaliação de prompts.

Este módulo contém a lógica principal para avaliar e otimizar prompts
de acordo com critérios predefinidos.
"""

import os
import re
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
from schemas.prompt_schema import PromptBase, PromptEvaluation, PlanType
from services.usage_manager import usage_manager
from utils.logger import logger
from config.settings import ASSISTANTS


load_dotenv()


class PromptEvaluator:
    """Classe responsável pela avaliação e otimização de prompts."""

    def __init__(self):
        """Inicializa o avaliador de prompts."""
        self.openai_client = None
        self.assistant_id = None
        self.free_api_key = os.getenv("OPENAI_API_KEY_FREE")

    def _initialize_client(self, plan_type: str = "free") -> OpenAI:
        """
        Inicializa o cliente OpenAI com a chave API apropriada.

        Args:
            plan_type: Tipo do plano ("free" ou "premium")

        Returns:
            OpenAI: Cliente OpenAI inicializado
        """
        try:
            if not os.path.exists(".env"):
                logger.error("Arquivo .env não encontrado")
                raise ValueError("Arquivo de configuração não encontrado")

            load_dotenv(override=True)

            api_key = os.getenv("OPENAI_API_KEY_FREE")
            if plan_type == "premium":
                api_key = os.getenv("OPENAI_API_KEY")

            if not api_key:
                logger.error("Chave API não encontrada no ambiente")
                raise ValueError("Chave API não encontrada")

            if not api_key.startswith("sk-"):
                logger.error("Formato inválido da chave API")
                raise ValueError("Formato inválido da chave API")

            logger.info(f"Inicializando cliente OpenAI para plano: {plan_type}")

            client = OpenAI(api_key=api_key)

            self.assistant_id = ASSISTANTS[plan_type]["id"]
            if not self.assistant_id:
                raise ValueError(f"ID do Assistant {plan_type} não encontrado")
            logger.info(f"Assistant ID configurado: {self.assistant_id}")

            return client

        except Exception as e:
            logger.error(f"Erro ao inicializar cliente OpenAI: {str(e)}")
            raise

    async def _get_evaluation_from_assistant(
        self, prompt: str, context: str = None
    ) -> Dict[str, Any]:
        """
        Obtém uma avaliação do prompt usando o OpenAI Assistant.
        
        Args:
            prompt: O prompt a ser avaliado
            context: Contexto adicional, se houver
            
        Returns:
            dict: Resultado da avaliação
        """
        try:
            logger.info("Iniciando thread de avaliação com Assistant")
            thread = await self.openai_client.beta.threads.create()
            
            # Formata a mensagem com prompt e contexto
            target_llm = getattr(prompt, 'target_llm', None) if hasattr(prompt, 'target_llm') else None
            prompt_content = prompt if isinstance(prompt, str) else prompt.content
            prompt_context = context if isinstance(prompt, str) else getattr(prompt, 'context', None)
            
            message_content = f"Por favor, avalie o seguinte prompt para ser utilizado com o modelo {target_llm or 'não especificado'}:\n\n{prompt_content}"
            if prompt_context:
                message_content += f"\n\nContexto adicional: {prompt_context}"
            
            logger.info("Adicionando mensagem à thread")
            message = await self.openai_client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message_content
            )
            
            # Inicia a execução
            logger.info(f"Executando o assistant {self.assistant_id}")
            run = await self.openai_client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Monitora a execução
            while run.status not in ["completed", "failed", "cancelled", "expired"]:
                logger.info(f"Verificando status: {run.status}")
                await asyncio.sleep(0.5)
                run = await self.openai_client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            # Verifica se houve falha na execução
            if run.status != "completed":
                logger.error(f"Execução falhou com status: {run.status}")
                raise ValueError(f"Falha na execução do assistant: {run.status}")
                
            # Obtém as mensagens
            logger.info("Recuperando mensagem de resposta")
            messages = await self.openai_client.beta.threads.messages.list(
                thread_id=thread.id
            )
            
            # Filtra a última mensagem do assistente
            assistant_message = None
            for message in messages.data:
                if message.role == "assistant":
                    assistant_message = message
                    break
                    
            if not assistant_message:
                logger.error("Mensagem do assistente não encontrada")
                raise ValueError("Mensagem do assistente não encontrada")
                
            content = assistant_message.content[0].text.value
            return self._parse_openai_response(content)
            
        except Exception as e:
            logger.error(f"Erro ao obter avaliação: {str(e)}")
            return {
                "scores": {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0},
                "suggestions": [f"Erro na avaliação: {str(e)}"],
                "optimized_prompt": prompt if isinstance(prompt, str) else prompt.content,
                "error": "evaluation_failed"
            }

    def _parse_openai_response(self, content: str) -> Dict[str, Any]:
        """
        Processa a resposta do OpenAI e extrai as pontuações e sugestões.

        Args:
            content: String contendo a resposta do OpenAI.

        Returns:
            Dict[str, Any]: Dicionário com os resultados processados.
        """
        try:
            clarity_match = re.search(r"CLAREZA:?\s*(\d+)", content, re.IGNORECASE)
            context_match = re.search(r"CONTEXTO:?\s*(\d+)", content, re.IGNORECASE)
            effectiveness_match = re.search(
                r"EFIC[AÁ]CIA:?\s*(\d+)", content, re.IGNORECASE
            )

            if not all([clarity_match, context_match, effectiveness_match]):
                logger.error(
                    "Não foi possível encontrar todas as pontuações na resposta"
                )
                logger.debug(f"Conteúdo recebido: {content}")
                logger.debug(
                    f"Matches: {clarity_match}, {context_match}, {effectiveness_match}"
                )
                return self._get_default_evaluation()

            suggestions = []
            suggestions_section = re.search(
                r"SUGEST[ÕO]ES:?\s*((?:[-•]\s*[^\n]+\n?)+)",
                content,
                re.IGNORECASE | re.MULTILINE,
            )
            if suggestions_section:
                suggestions = re.findall(
                    r"[-•]\s*([^\n]+)", suggestions_section.group(1)
                )

            if not suggestions:
                suggestions = ["Nenhuma sugestão disponível"]

            optimized_match = re.search(
                r"PROMPT\s*OTIMIZADO:?\s*([^\n]+(?:\n[^\n]+)*?)(?:\n\s*VERS[ÕO]ES|$)",
                content,
                re.IGNORECASE | re.MULTILINE | re.DOTALL,
            )
            optimized_prompt = (
                optimized_match.group(1).strip() if optimized_match else None
            )

            improved_versions = []
            versions_section = re.search(
                r"VERS[ÕO]ES\s*MELHORADAS:?\s*((?:\d+\.\s*[^\n]+\n?)+)",
                content,
                re.IGNORECASE | re.MULTILINE,
            )
            if versions_section:
                improved_versions = re.findall(
                    r"\d+\.\s*([^\n]+)", versions_section.group(1)
                )

            clarity = int(clarity_match.group(1))
            context = int(context_match.group(1))
            effectiveness = int(effectiveness_match.group(1))
            average = (clarity + context + effectiveness) / 3

            return {
                "scores": {
                    "clarity": clarity,
                    "context": context,
                    "effectiveness": effectiveness,
                    "average": round(average, 2),
                },
                "suggestions": suggestions,
                "optimized_prompt": optimized_prompt
                or "Não foi possível gerar um prompt otimizado",
                "improved_versions": improved_versions,
            }

        except Exception as e:
            logger.error(f"Erro ao processar resposta do OpenAI: {str(e)}")
            return self._get_default_evaluation()

    def _get_default_evaluation(self) -> Dict[str, Any]:
        """
        Retorna uma avaliação padrão em caso de erro.

        Returns:
            Dict[str, Any]: Avaliação padrão.
        """
        return {
            "scores": {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0},
            "suggestions": [
                "Não foi possível avaliar o prompt. Por favor, tente novamente."
            ],
            "optimized_prompt": "Não foi possível otimizar o prompt",
        }

    async def evaluate(self, prompt: PromptBase) -> PromptEvaluation:
        """
        Avalia um prompt usando o plano especificado.

        Args:
            prompt: Objeto PromptBase contendo o prompt e metadados.

        Returns:
            PromptEvaluation: Resultado da avaliação.
        """
        try:
            logger.info(f"Iniciando avaliação - Plano: {prompt.plan_type}")

            if not prompt.content or not isinstance(prompt.content, str):
                raise ValueError("Conteúdo do prompt inválido")

            cleaned_content = prompt.content.strip()
            if not cleaned_content:
                raise ValueError("Conteúdo do prompt vazio após limpeza")

            user_id = getattr(prompt, "user_id", None)
            if not user_id:
                raise ValueError("ID do usuário necessário")

            if prompt.plan_type == PlanType.PREMIUM:
                can_use, message, has_expired = usage_manager.can_use_premium(user_id)
                if not can_use:
                    raise ValueError(message)
            else:
                can_use, message = usage_manager.can_use_free(user_id)
                if not can_use:
                    raise ValueError(message)

            logger.info("Inicializando cliente OpenAI para avaliação...")
            try:
                self.openai_client = self._initialize_client(
                    str(prompt.plan_type).split(".")[-1].lower()
                )
                if not self.openai_client:
                    raise ValueError("Cliente OpenAI não foi inicializado corretamente")
                logger.info("Cliente OpenAI inicializado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao inicializar cliente OpenAI: {str(e)}")
                if "insufficient_quota" in str(e):
                    raise ValueError(
                        "O serviço está temporariamente indisponível. Por favor, tente novamente mais tarde ou considere usar o plano premium."
                    )
                raise ValueError(f"Erro ao inicializar cliente OpenAI: {str(e)}")

            result = None
            try:
                if prompt.plan_type == PlanType.PREMIUM:
                    self.assistant_id = ASSISTANTS["premium"]["id"]
                else:
                    self.assistant_id = ASSISTANTS["free"]["id"]

                if not self.assistant_id:
                    raise ValueError(
                        f"ID do Assistant não encontrado para o plano {prompt.plan_type}"
                    )

                result = await self._get_evaluation_from_assistant(
                    cleaned_content, prompt.context
                )

            except Exception as e:
                if "insufficient_quota" in str(e):
                    raise ValueError(
                        "O serviço está temporariamente indisponível. Por favor, tente novamente mais tarde ou considere usar o plano premium."
                    )
                raise e

            if prompt.plan_type == PlanType.PREMIUM:
                usage_manager.register_premium_usage(user_id)
            else:
                usage_manager.register_free_usage(user_id)

            return PromptEvaluation(
                clarity_score=float(result["scores"]["clarity"]),
                context_score=float(result["scores"]["context"]),
                effectiveness_score=float(result["scores"]["effectiveness"]),
                suggestions=result["suggestions"],
                optimized_prompt=result["optimized_prompt"],
            )

        except Exception as e:
            logger.error(f"Erro na avaliação do prompt: {str(e)}")
            if "insufficient_quota" in str(e):
                raise ValueError(
                    "O serviço está temporariamente indisponível. Por favor, tente novamente mais tarde ou considere usar o plano premium."
                )
            raise ValueError(str(e))

    async def evaluate_prompt(
        self,
        prompt: str,
        context: str = None,
        target_model: str = "gpt-4",
        plan_type: str = "free",
        user_id: str = None,
    ) -> dict:
        """
        Avalia um prompt usando GPT-3.5 (free) ou Assistant especializado (premium)
        """
        try:
            if not prompt:
                raise ValueError("Prompt não pode estar vazio")

            if plan_type == "premium":
                if not user_id:
                    return {
                        "scores": {
                            "clarity": 0,
                            "context": 0,
                            "effectiveness": 0,
                            "average": 0,
                        },
                        "suggestions": [
                            "Por favor, faça login para usar o plano premium."
                        ],
                        "optimized_prompt": prompt,
                        "improved_versions": [],
                        "premium_status": "Login necessário para usar o plano premium",
                    }

                can_use, message, has_expired = usage_manager.can_use_premium(user_id)
                if not can_use:
                    return {
                        "scores": {
                            "clarity": 0,
                            "context": 0,
                            "effectiveness": 0,
                            "average": 0,
                        },
                        "suggestions": [message],
                        "optimized_prompt": prompt,
                        "improved_versions": [],
                        "premium_status": message,
                    }

            try:
                self.openai_client = self._initialize_client(plan_type)
                if not self.openai_client:
                    raise ValueError("Cliente OpenAI não foi inicializado corretamente")

            except Exception as e:
                if "insufficient_quota" in str(e):
                    return {
                        "scores": {
                            "clarity": 0,
                            "context": 0,
                            "effectiveness": 0,
                            "average": 0,
                        },
                        "suggestions": [
                            "O serviço gratuito está temporariamente indisponível. Por favor, tente novamente mais tarde ou considere usar o plano premium."
                        ],
                        "optimized_prompt": prompt,
                        "improved_versions": [],
                        "error": "quota_exceeded",
                    }
                return self._get_default_evaluation()

            result = None
            try:
                if plan_type == "premium":
                    result = await self._get_evaluation_from_assistant(prompt, context)
                    if result and not result.get("error"):
                        usage_manager.register_premium_usage(user_id)
                else:
                    result = await self._get_evaluation_from_assistant(prompt, context)
                    if result and not result.get("error"):
                        usage_manager.register_free_usage(user_id)
            except Exception as e:
                if "insufficient_quota" in str(e):
                    return {
                        "scores": {
                            "clarity": 0,
                            "context": 0,
                            "effectiveness": 0,
                            "average": 0,
                        },
                        "suggestions": [
                            "O serviço gratuito está temporariamente indisponível. Por favor, tente novamente mais tarde ou considere usar o plano premium."
                        ],
                        "optimized_prompt": prompt,
                        "improved_versions": [],
                        "error": "quota_exceeded",
                    }
                return self._get_default_evaluation()

            if plan_type == "premium" and user_id:
                _, status_message, _ = usage_manager.can_use_premium(user_id)
                result["premium_status"] = status_message

            if not result or not isinstance(result, dict):
                return self._get_default_evaluation()

            result.setdefault(
                "scores", {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0}
            )
            result.setdefault("suggestions", ["Nenhuma sugestão disponível"])
            result.setdefault("optimized_prompt", prompt)
            result.setdefault("improved_versions", [])

            return result

        except Exception as e:
            if "insufficient_quota" in str(e):
                return {
                    "scores": {
                        "clarity": 0,
                        "context": 0,
                        "effectiveness": 0,
                        "average": 0,
                    },
                    "suggestions": [
                        "O serviço gratuito está temporariamente indisponível. Por favor, tente novamente mais tarde ou considere usar o plano premium."
                    ],
                    "optimized_prompt": prompt,
                    "improved_versions": [],
                    "error": "quota_exceeded",
                }
            return self._get_default_evaluation()
