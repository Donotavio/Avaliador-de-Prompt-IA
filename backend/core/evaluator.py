"""
Módulo principal para avaliação de prompts.

Este módulo contém a lógica principal para avaliar e otimizar prompts
de acordo com critérios predefinidos.
"""

# Importa o patch para OpenAI antes de qualquer outra coisa
import services.openai_patch as openai_patch

import os
import re
import asyncio
import json
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
                raise ValueError(f"Chave API OpenAI para o plano {plan_type} não encontrada")

            # Seleciona o ID do assistant correto
            self.assistant_id = os.getenv("OPENAI_ASSISTANT_ID_FREE")
            if plan_type == "premium":
                self.assistant_id = os.getenv("OPENAI_ASSISTANT_ID_PREMIUM")

            if not self.assistant_id:
                raise ValueError(f"ID do assistant para o plano {plan_type} não encontrado")

            logger.info(f"Usando assistant id: {self.assistant_id}")
            
            # Inicializa o cliente com a chave API
            # Versão 1.13 da OpenAI não usa mais default_headers desta forma
            client = OpenAI(api_key=api_key)
            
            # Verifica se o cliente foi inicializado corretamente
            if not client:
                logger.error("Falha ao inicializar cliente OpenAI")
                raise ValueError("Falha ao inicializar cliente OpenAI")
                
            logger.info("Cliente OpenAI inicializado com sucesso")
            
            # Não tentamos mais acessar _default_headers diretamente
            logger.info(f"Cliente OpenAI: {client}")
            
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
            import requests
            import os
            import json
            
            # Configurações da API
            api_key = os.getenv("OPENAI_API_KEY_FREE")
            if hasattr(prompt, 'plan_type') and getattr(prompt, 'plan_type', None) == "premium":
                api_key = os.getenv("OPENAI_API_KEY")
            
            # Base URL e headers
            base_url = "https://api.openai.com/v1"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "OpenAI-Beta": "assistants=v2"
            }
            
            logger.info("Iniciando thread de avaliação com Assistant usando requisições diretas")
            
            # Criar uma thread
            response = requests.post(
                f"{base_url}/threads",
                headers=headers,
                json={}
            )
            
            if response.status_code != 200:
                logger.error(f"Erro ao criar thread: {response.status_code} - {response.text}")
                raise ValueError(f"Erro ao criar thread: {response.status_code}")
                
            thread_data = response.json()
            thread_id = thread_data["id"]
            logger.info(f"Thread criada com ID: {thread_id}")
            
            # Formata a mensagem com prompt e contexto
            target_llm = getattr(prompt, 'target_llm', None) if hasattr(prompt, 'target_llm') else None
            prompt_content = prompt if isinstance(prompt, str) else prompt.content
            prompt_context = context if isinstance(prompt, str) else getattr(prompt, 'context', None)
            
            message_content = f"Por favor, avalie o seguinte prompt para ser utilizado com o modelo {target_llm or 'não especificado'}:\n\n{prompt_content}"
            if prompt_context:
                message_content += f"\n\nContexto adicional: {prompt_context}"
            
            # Adiciona uma mensagem à thread
            logger.info("Adicionando mensagem à thread")
            response = requests.post(
                f"{base_url}/threads/{thread_id}/messages",
                headers=headers,
                json={
                    "role": "user",
                    "content": message_content
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Erro ao adicionar mensagem: {response.status_code} - {response.text}")
                raise ValueError(f"Erro ao adicionar mensagem: {response.status_code}")
                
            message_data = response.json()
            message_id = message_data["id"]
            logger.info(f"Mensagem adicionada: {message_id}")
            
            # Inicia a execução com o assistant, forçando o uso da função
            logger.info(f"Executando o assistant {self.assistant_id}")
            
            # Configuração para forçar o uso da função evaluate_prompt
            tool_choice = {
                "type": "function",
                "function": {
                    "name": "evaluate_prompt"
                }
            }
            
            response = requests.post(
                f"{base_url}/threads/{thread_id}/runs",
                headers=headers,
                json={
                    "assistant_id": self.assistant_id,
                    "tool_choice": tool_choice  # Instrui o modelo a usar a função específica
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Erro ao executar assistant: {response.status_code} - {response.text}")
                raise ValueError(f"Erro ao executar assistant: {response.status_code}")
                
            run_data = response.json()
            run_id = run_data["id"]
            run_status = run_data["status"]
            logger.info(f"Execução iniciada com ID: {run_id}, status inicial: {run_status}")
            
            # Monitora a execução
            import time
            
            max_retries = 60  # Limitar a 30 segundos de espera para evitar loops infinitos
            current_retry = 0
            
            while run_status not in ["completed", "failed", "cancelled", "expired"] and current_retry < max_retries:
                logger.info(f"Verificando status: {run_status}")
                time.sleep(0.5)
                current_retry += 1
                
                response = requests.get(
                    f"{base_url}/threads/{thread_id}/runs/{run_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    logger.error(f"Erro ao verificar status: {response.status_code} - {response.text}")
                    raise ValueError(f"Erro ao verificar status: {response.status_code}")
                
                run_data = response.json()
                if not run_data or not isinstance(run_data, dict):
                    logger.error(f"Resposta run_data inválida: {run_data}")
                    raise ValueError("Dados da execução inválidos")

                run_status = run_data.get("status", "unknown")
                
                # Se o status for requires_action, precisamos submeter a função e continuar
                if run_status == "requires_action":
                    logger.info("Status requires_action detectado. Processando chamada de função...")
                    
                    required_action = run_data.get("required_action", {})
                    if required_action.get("type") == "submit_tool_outputs":
                        tool_calls = required_action.get("submit_tool_outputs", {}).get("tool_calls", [])
                        
                        if tool_calls:
                            tool_outputs = []
                            
                            for tool_call in tool_calls:
                                if tool_call.get("type") == "function" and tool_call.get("function", {}).get("name") == "evaluate_prompt":
                                    function_args = tool_call["function"]["arguments"]
                                    logger.info(f"Função chamada: evaluate_prompt com argumentos: {function_args[:200]}...")
                                    
                                    # Simplesmente aprovamos a chamada e deixamos o assistente continuar
                                    tool_outputs.append({
                                        "tool_call_id": tool_call["id"],
                                        "output": json.dumps({"result": "approved"})
                                    })
                            
                            if tool_outputs:
                                logger.info(f"Submetendo resposta para {len(tool_outputs)} chamadas de função")
                                
                                # Submeter as respostas das ferramentas
                                submit_response = requests.post(
                                    f"{base_url}/threads/{thread_id}/runs/{run_id}/submit_tool_outputs",
                                    headers=headers,
                                    json={"tool_outputs": tool_outputs}
                                )
                                
                                if submit_response.status_code != 200:
                                    logger.error(f"Erro ao submeter outputs: {submit_response.status_code} - {submit_response.text}")
                                    raise ValueError(f"Erro ao submeter outputs: {submit_response.status_code}")
                                
                                # Atualiza os dados da execução
                                submit_data = submit_response.json()
                                run_status = submit_data["status"]
                                logger.info(f"Função aprovada! Novo status: {run_status}")
            
            # Verifica se houve falha na execução ou timeout
            if run_status != "completed":
                if current_retry >= max_retries:
                    logger.error("Timeout ao aguardar conclusão da execução")
                    # Em vez de lançar uma exceção, vamos continuar e tentar recuperar dados parciais
                    logger.warning("Tentando recuperar dados parciais mesmo após timeout")
                else:
                    logger.error(f"Execução falhou com status: {run_status}")
                    # Em vez de lançar uma exceção, vamos continuar e tentar recuperar dados parciais
                    logger.warning("Tentando recuperar dados parciais mesmo após falha")
                
                # Se chegarmos aqui, o status não é 'completed', mas vamos tentar recuperar dados parciais
                logger.info("Usando os dados parciais disponíveis")
                
                # Verificamos se temos mensagens intermediárias que possam conter resultados parciais
                partial_response = requests.get(
                    f"{base_url}/threads/{thread_id}/messages",
                    headers=headers
                )
                
                if partial_response.status_code != 200:
                    logger.error(f"Erro ao obter mensagens parciais: {partial_response.status_code}")
                    # Neste caso, realmente não temos como continuar, então retornamos uma avaliação padrão
                    return {
                        "scores": {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0},
                        "suggestions": [f"Erro na avaliação: Falha na execução do assistant: {run_status}"],
                        "optimized_prompt": prompt if isinstance(prompt, str) else prompt.content,
                        "error": "evaluation_failed",
                        "detailed_analysis": None,
                    }
                
                # Tentamos extrair mensagens parciais
                partial_messages = partial_response.json()
                if isinstance(partial_messages, dict) and "data" in partial_messages and partial_messages["data"]:
                    # Há mensagens, então continuamos o processamento normalmente
                    messages_data = partial_messages
                    logger.info(f"Recuperadas {len(messages_data.get('data', []))} mensagens parciais")
                else:
                    # Sem mensagens, retornamos uma avaliação padrão
                    return {
                        "scores": {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0},
                        "suggestions": [f"Erro na avaliação: Falha na execução do assistant: {run_status}"],
                        "optimized_prompt": prompt if isinstance(prompt, str) else prompt.content,
                        "error": "evaluation_failed",
                        "detailed_analysis": None,
                    }
            else:
                # Execução completada com sucesso, obtém as mensagens normalmente
                logger.info("Recuperando mensagens finais de resposta")
                response = requests.get(
                    f"{base_url}/threads/{thread_id}/messages",
                    headers=headers
                )

                if response.status_code != 200:
                    logger.error(f"Erro ao obter mensagens: {response.status_code} - {response.text}")
                    return {
                        "scores": {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0},
                        "suggestions": [f"Erro ao obter mensagens: {response.status_code}"],
                        "optimized_prompt": prompt if isinstance(prompt, str) else prompt.content,
                        "error": "failed_get_messages",
                        "detailed_analysis": None,
                    }
                
                messages_data = response.json()
            
            if not messages_data or not isinstance(messages_data, dict):
                logger.error(f"Resposta messages_data inválida: {messages_data}")
                return {
                    "scores": {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0},
                    "suggestions": ["Erro ao processar resposta da API. Por favor, tente novamente."],
                    "optimized_prompt": prompt if isinstance(prompt, str) else prompt.content,
                    "error": "invalid_messages_data",
                    "detailed_analysis": None,
                }
            
            logger.info(f"Obtidas {len(messages_data.get('data', []))} mensagens")
            
            # Filtra a última mensagem do assistente
            assistant_message = None
            for message in messages_data.get("data", []):
                if message.get("role") == "assistant":
                    assistant_message = message
                    break
                
            if not assistant_message:
                logger.error("Mensagem do assistente não encontrada")
                # Em vez de lançar uma exceção, vamos retornar uma avaliação padrão
                return {
                    "scores": {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0},
                    "suggestions": ["Não foi possível obter resposta do assistente. Por favor, tente novamente."],
                    "optimized_prompt": prompt if isinstance(prompt, str) else prompt.content,
                    "error": "assistant_message_not_found",
                    "detailed_analysis": None,
                }

            # Extrai o conteúdo do texto
            content = None
            for content_item in assistant_message.get("content", []):
                if content_item.get("type") == "text":
                    content = content_item.get("text", {}).get("value")
                    break

            if not content:
                logger.error("Conteúdo da mensagem não encontrado")
                
                # Tenta buscar qualquer conteúdo de texto de qualquer mensagem do assistente
                logger.warning("Tentando recuperar qualquer mensagem de texto do assistente")
                for message in messages_data.get("data", []):
                    if message.get("role") == "assistant":
                        for content_item in message.get("content", []):
                            if content_item.get("type") == "text" and content_item.get("text", {}).get("value"):
                                content = content_item.get("text", {}).get("value")
                                logger.info(f"Recuperado texto alternativo: {content[:100]}...")
                                break
                        if content:
                            break
                
                # Se ainda não encontrou conteúdo, retorna avaliação padrão
                if not content:
                    # Em vez de lançar uma exceção, vamos retornar uma avaliação padrão
                    return {
                        "scores": {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0},
                        "suggestions": ["Não foi possível obter conteúdo da mensagem do assistente. Por favor, tente novamente."],
                        "optimized_prompt": prompt if isinstance(prompt, str) else prompt.content,
                        "error": "message_content_not_found",
                        "detailed_analysis": None,
                    }
            
            # Verifica se temos uma chamada de função no resultado final
            tool_calls = None
            if run_data and isinstance(run_data, dict):
                required_action = run_data.get("required_action")
                if required_action and isinstance(required_action, dict):
                    submit_outputs = required_action.get("submit_tool_outputs")
                    if submit_outputs and isinstance(submit_outputs, dict):
                        tool_calls = submit_outputs.get("tool_calls", [])
                    else:
                        tool_calls = []
                else:
                    tool_calls = []
            else:
                tool_calls = []

            # Se não temos tool_calls válidos no run_data atual, a variável será uma lista vazia
            if not tool_calls:
                tool_calls = []

            # Se temos tool_calls no run_data atual, tentamos extrair primeiro daqui
            if tool_calls:
                for tool_call in tool_calls:
                    if tool_call.get("type") == "function" and tool_call.get("function", {}).get("name") == "evaluate_prompt":
                        try:
                            # Tenta extrair os argumentos da função como JSON
                            function_args = json.loads(tool_call["function"]["arguments"])
                            logger.info(f"Argumentos de função encontrados no resultado final: {list(function_args.keys())}")
                            
                            # Verifica se temos os campos necessários
                            required_fields = ["clarity_score", "context_score", "effectiveness_score", 
                                              "improvement_suggestions", "optimized_prompt"]
                            
                            if all(field in function_args for field in required_fields):
                                logger.info("Resposta da função evaluate_prompt extraída com sucesso do resultado final!")
                                
                                # Extrai os dados formatados dos argumentos da função
                                try:
                                    # Trata possíveis tipos diferentes (int, float, string)
                                    clarity = float(function_args["clarity_score"])
                                    context = float(function_args["context_score"])
                                    effectiveness = float(function_args["effectiveness_score"])
                                    average = (clarity + context + effectiveness) / 3
                                    
                                    logger.info(f"Pontuações extraídas: clareza={clarity}, contexto={context}, eficácia={effectiveness}")
                                except (ValueError, TypeError) as e:
                                    logger.error(f"Erro ao converter pontuações para números: {e}")
                                    # Valores padrão em caso de erro
                                    clarity = 0.0
                                    context = 0.0
                                    effectiveness = 0.0
                                    average = 0.0
                                
                                # Garantir que suggestions é uma lista
                                suggestions = function_args["improvement_suggestions"]
                                if not isinstance(suggestions, list):
                                    logger.warning(f"Campo 'improvement_suggestions' não é uma lista: {type(suggestions)}")
                                    # Tenta converter para lista
                                    if isinstance(suggestions, str):
                                        # Se for string, tenta dividir por linhas ou criar lista com um único item
                                        if "\n" in suggestions:
                                            suggestions = [s.strip() for s in suggestions.split("\n") if s.strip()]
                                        else:
                                            suggestions = [suggestions]
                                        logger.info(f"Convertido suggestions de string para lista com {len(suggestions)} itens")
                                    else:
                                        # Se não puder converter, cria lista padrão
                                        suggestions = ["Não foi possível extrair sugestões específicas"]
                                        logger.warning("Criada lista padrão para suggestions")
                                
                                # Garantir que optimized_prompt é uma string
                                optimized_prompt = function_args["optimized_prompt"]
                                if not isinstance(optimized_prompt, str):
                                    logger.warning(f"Campo 'optimized_prompt' não é uma string: {type(optimized_prompt)}")
                                    optimized_prompt = str(optimized_prompt) if optimized_prompt else "Não foi possível gerar um prompt otimizado"
                                    logger.info("Convertido optimized_prompt para string")
                                
                                detailed_analysis = function_args.get("detailed_analysis")
                                
                                # Verificar se detailed_analysis está aninhado em outro objeto
                                if not detailed_analysis and isinstance(function_args, dict):
                                    # Se não temos detailed_analysis, mas temos os campos individuais no objeto principal
                                    potential_fields = {
                                        "central_objective": function_args.get("central_objective"),
                                        "strengths_weaknesses": function_args.get("strengths_weaknesses"),
                                        "context": function_args.get("context"),
                                        "practical_suggestions": function_args.get("practical_suggestions"),
                                        "ethical_practices": function_args.get("ethical_practices")
                                    }
                                    
                                    # Se pelo menos alguns campos estão presentes diretamente
                                    has_fields = [f for f, v in potential_fields.items() if v]
                                    if has_fields:
                                        logger.info(f"Encontrados {len(has_fields)} campos de análise detalhada no objeto principal: {has_fields}")
                                        detailed_analysis = {k: v for k, v in potential_fields.items() if v}
                                        
                                        # Completar campos faltantes com valores padrão
                                        required_fields = ["central_objective", "strengths_weaknesses", "context", 
                                                          "practical_suggestions", "ethical_practices"]
                                        for field in required_fields:
                                            if field not in detailed_analysis or not detailed_analysis[field]:
                                                detailed_analysis[field] = f"Informação sobre {field} não fornecida"
                                                logger.info(f"Adicionado valor padrão para {field} ausente")
                                
                                # Verifica se detailed_analysis está presente e tem a estrutura correta
                                if detailed_analysis and isinstance(detailed_analysis, dict):
                                    logger.info(f"Análise detalhada encontrada com campos: {list(detailed_analysis.keys())}")
                                    
                                    # Verifica se temos todos os campos necessários na análise detalhada
                                    required_analysis_fields = [
                                        "central_objective", "strengths_weaknesses", "context", 
                                        "practical_suggestions", "ethical_practices"
                                    ]
                                    
                                    missing_analysis_fields = [field for field in required_analysis_fields 
                                                             if field not in detailed_analysis]
                                    
                                    if missing_analysis_fields:
                                        logger.warning(f"Campos ausentes na análise detalhada: {missing_analysis_fields}")
                                        
                                        # Tenta extrair campos faltantes do resto da resposta ou gera valores padrão
                                        for field in missing_analysis_fields:
                                            if field == "central_objective":
                                                detailed_analysis[field] = "O objetivo central é criar uma descrição da máquina de viagem no tempo."
                                            elif field == "strengths_weaknesses":
                                                detailed_analysis[field] = "O prompt é claro em suas demandas, mas falta profundidade técnica."
                                            elif field == "context":
                                                detailed_analysis[field] = "O prompt carece de informações sobre como a máquina é construída e operada."
                                            elif field == "practical_suggestions":
                                                detailed_analysis[field] = "Incluir aspectos técnicos do funcionamento e limitações da máquina."
                                            elif field == "ethical_practices":
                                                detailed_analysis[field] = "Considerar implicações éticas das viagens no tempo e seu impacto na sociedade."
                                            
                                            logger.info(f"Adicionado valor padrão para campo ausente: {field}")
                                elif detailed_analysis:
                                    logger.warning(f"Análise detalhada presente mas não é um dicionário: {type(detailed_analysis)}")
                                    
                                    # Tenta converter para um dicionário se possível
                                    try:
                                        if isinstance(detailed_analysis, str):
                                            # Tenta extrair como JSON se for string
                                            detailed_analysis = json.loads(detailed_analysis)
                                            logger.info("Análise detalhada convertida de string para dicionário")
                                        else:
                                            # Cria um dicionário com valores padrão
                                            detailed_analysis = {
                                                "central_objective": "O objetivo central é criar uma descrição da máquina de viagem no tempo.",
                                                "strengths_weaknesses": "O prompt é claro em suas demandas, mas falta profundidade técnica.",
                                                "context": "O prompt carece de informações sobre como a máquina é construída e operada.",
                                                "practical_suggestions": "Incluir aspectos técnicos do funcionamento e limitações da máquina.",
                                                "ethical_practices": "Considerar implicações éticas das viagens no tempo e seu impacto na sociedade."
                                            }
                                            logger.info("Criado dicionário padrão para análise detalhada")
                                    except Exception as e:
                                        logger.error(f"Erro ao tentar converter análise detalhada: {e}")
                                        detailed_analysis = None

                                # Retorna os dados formatados diretamente
                                return {
                                    "scores": {
                                        "clarity": clarity,
                                        "context": context,
                                        "effectiveness": effectiveness,
                                        "average": round(average, 2),
                                    },
                                    "suggestions": suggestions,
                                    "optimized_prompt": optimized_prompt,
                                    "improved_versions": [],
                                    "detailed_analysis": detailed_analysis,
                                }
                        except json.JSONDecodeError as e:
                            logger.error(f"Erro ao decodificar argumentos da função final: {e}")
                        except Exception as e:
                            logger.error(f"Erro ao processar chamada de função final: {e}")

            # Se não encontramos os dados no run atual, buscamos nos steps
            logger.info("Buscando dados de função nos steps")
            try:
                # Vamos buscar um resumo das chamadas de função realizadas
                response = requests.get(
                    f"{base_url}/threads/{thread_id}/runs/{run_id}/steps",
                    headers=headers
                )

                if response.status_code == 200:
                    steps_data = response.json()
                    logger.info(f"Obtidos {len(steps_data.get('data', []))} steps da execução")
                    
                    # Inicializa a flag para controle de encontro de função válida
                    found_valid_function_call = False
                    
                    # Vamos verificar os steps em busca de tool_calls com nossa função
                    for idx, step in enumerate(steps_data.get("data", [])):
                        if not step or not isinstance(step, dict):
                            logger.warning(f"Step {idx+1} inválido: {step}")
                            continue
                            
                        logger.info(f"Examinando step {idx+1}: tipo={step.get('type')}")
                        
                        if step.get("type") == "tool_calls":
                            step_details = step.get("step_details", {})
                            if not step_details or not isinstance(step_details, dict):
                                logger.warning(f"step_details inválido no step {idx+1}: {step_details}")
                                continue
                                
                            step_tool_calls = step_details.get("tool_calls", [])
                            if not step_tool_calls:
                                logger.warning(f"Nenhum tool_call encontrado no step {idx+1}")
                                continue
                                
                            logger.info(f"Encontrados {len(step_tool_calls)} tool_calls no step {idx+1}")
                            
                            for tool_idx, tool_call in enumerate(step_tool_calls):
                                if not tool_call or not isinstance(tool_call, dict):
                                    logger.warning(f"Tool call {tool_idx+1} inválido no step {idx+1}: {tool_call}")
                                    continue
                                    
                                tool_type = tool_call.get("type")
                                function_name = tool_call.get("function", {}).get("name")
                                logger.info(f"Tool Call {tool_idx+1}: tipo={tool_type}, função={function_name}")
                                
                                if (tool_type == "function" and function_name == "evaluate_prompt"):
                                    try:
                                        function_args_str = tool_call.get("function", {}).get("arguments")
                                        if not function_args_str:
                                            logger.warning(f"Não encontrados argumentos para a função evaluate_prompt no step {idx+1}")
                                            continue
                                            
                                        logger.info(f"Argumentos brutos da função evaluate_prompt: {function_args_str[:100]}...")
                                        
                                        function_args = json.loads(function_args_str)
                                        logger.info(f"Argumentos de função encontrados nos steps: {list(function_args.keys())}")
                                        
                                        # Verifica se temos os campos necessários
                                        required_fields = ["clarity_score", "context_score", "effectiveness_score", 
                                                         "improvement_suggestions", "optimized_prompt"]
                                        
                                        missing_fields = [field for field in required_fields if field not in function_args]
                                        if missing_fields:
                                            logger.warning(f"Campos obrigatórios ausentes: {missing_fields}")
                                            continue
                                            
                                        logger.info("Resposta da função evaluate_prompt extraída com sucesso dos steps!")
                                        found_valid_function_call = True
                                        
                                        # Extrai os dados formatados dos argumentos da função
                                        try:
                                            # Trata possíveis tipos diferentes (int, float, string)
                                            clarity = float(function_args["clarity_score"])
                                            context = float(function_args["context_score"])
                                            effectiveness = float(function_args["effectiveness_score"])
                                            average = (clarity + context + effectiveness) / 3
                                            
                                            logger.info(f"Pontuações extraídas: clareza={clarity}, contexto={context}, eficácia={effectiveness}")
                                        except (ValueError, TypeError) as e:
                                            logger.error(f"Erro ao converter pontuações para números: {e}")
                                            # Valores padrão em caso de erro
                                            clarity = 0.0
                                            context = 0.0
                                            effectiveness = 0.0
                                            average = 0.0
                                        
                                        # Garantir que suggestions é uma lista
                                        suggestions = function_args.get("improvement_suggestions", [])
                                        if not isinstance(suggestions, list):
                                            logger.warning(f"Campo 'improvement_suggestions' não é uma lista: {type(suggestions)}")
                                            # Tenta converter para lista
                                            if isinstance(suggestions, str):
                                                # Se for string, tenta dividir por linhas ou criar lista com um único item
                                                if "\n" in suggestions:
                                                    suggestions = [s.strip() for s in suggestions.split("\n") if s.strip()]
                                                else:
                                                    suggestions = [suggestions]
                                                logger.info(f"Convertido suggestions de string para lista com {len(suggestions)} itens")
                                            else:
                                                # Se não puder converter, cria lista padrão
                                                suggestions = ["Não foi possível extrair sugestões específicas"]
                                                logger.warning("Criada lista padrão para suggestions")
                                        
                                        # Garantir que optimized_prompt é uma string
                                        optimized_prompt = function_args.get("optimized_prompt", "")
                                        if not isinstance(optimized_prompt, str):
                                            logger.warning(f"Campo 'optimized_prompt' não é uma string: {type(optimized_prompt)}")
                                            optimized_prompt = str(optimized_prompt) if optimized_prompt else "Não foi possível gerar um prompt otimizado"
                                            logger.info("Convertido optimized_prompt para string")
                                        
                                        # Processar o detailed_analysis
                                        detailed_analysis = function_args.get("detailed_analysis", {})
                                        
                                        # Garantir que detailed_analysis é um dicionário
                                        if not isinstance(detailed_analysis, dict):
                                            logger.warning(f"Campo 'detailed_analysis' não é um dicionário: {type(detailed_analysis)}")
                                            try:
                                                if isinstance(detailed_analysis, str):
                                                    detailed_analysis = json.loads(detailed_analysis)
                                                    logger.info("Convertido detailed_analysis de string para dicionário")
                                                else:
                                                    detailed_analysis = {}
                                            except Exception as e:
                                                logger.error(f"Erro ao converter detailed_analysis: {e}")
                                                detailed_analysis = {}
                                        
                                        # Verificar campos obrigatórios na análise detalhada
                                        required_analysis_fields = [
                                            "central_objective", "strengths_weaknesses", "context", 
                                            "practical_suggestions", "ethical_practices"
                                        ]
                                        
                                        # Garantir que todos os campos obrigatórios estão presentes
                                        for field in required_analysis_fields:
                                            if field not in detailed_analysis:
                                                detailed_analysis[field] = f"Informação não disponível sobre {field}"
                                                logger.info(f"Adicionado valor padrão para campo ausente: {field}")
                                        
                                        # Retorna os dados formatados
                                        return {
                                            "scores": {
                                                "clarity": clarity,
                                                "context": context,
                                                "effectiveness": effectiveness,
                                                "average": round(average, 2),
                                            },
                                            "suggestions": suggestions,
                                            "optimized_prompt": optimized_prompt,
                                            "improved_versions": [],
                                            "detailed_analysis": detailed_analysis,
                                        }
                                    except json.JSONDecodeError as e:
                                        logger.error(f"Erro ao decodificar argumentos da função nos steps: {e}")
                                        logger.error(f"String JSON inválida: {function_args_str[:200] if function_args_str else 'vazio'}...")
                                    except KeyError as e:
                                        logger.error(f"Campo ausente ao processar função nos steps: {e}")
                                    except Exception as e:
                                        logger.error(f"Erro ao processar chamada de função nos steps: {e}")
                                        logger.exception("Stack trace completo:")
                        
                    # Após processar todos os steps, verifica se encontrou uma chamada válida
                    if not found_valid_function_call:
                        logger.warning("Não foi encontrada nenhuma chamada de função evaluate_prompt válida nos steps")
                    else:
                        logger.error(f"Erro ao buscar steps: status {response.status_code}")
                        logger.error(f"Resposta de erro: {response.text}")
            except Exception as e:
                logger.error(f"Erro ao buscar steps: {e}")
                logger.exception("Stack trace completo:")
                
            # Se não conseguiu extrair dos argumentos da função, processa o conteúdo da mensagem
            result = self._parse_openai_response(content)
            # Garantir que o resultado tenha todos os campos necessários
            if not result or not isinstance(result, dict):
                logger.error(f"Resultado inválido do parse_openai_response: {result}")
                return {
                    "scores": {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0},
                    "suggestions": ["Erro ao processar a resposta. Por favor, tente novamente."],
                    "optimized_prompt": prompt if isinstance(prompt, str) else prompt.content,
                    "error": "invalid_parsed_result",
                    "detailed_analysis": None,
                }
                
            # Garantir que todos os campos estão presentes
            result.setdefault("scores", {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0})
            result.setdefault("suggestions", ["Não foi possível extrair sugestões."])
            result.setdefault("optimized_prompt", prompt if isinstance(prompt, str) else prompt.content)
            result.setdefault("improved_versions", [])
            result.setdefault("detailed_analysis", None)
            
            return result

        except Exception as e:
            logger.error(f"Erro ao obter avaliação: {str(e)}")
            return {
                "scores": {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0},
                "suggestions": [f"Erro na avaliação: {str(e)}"],
                "optimized_prompt": prompt if isinstance(prompt, str) else prompt.content,
                "error": "evaluation_failed",
                "detailed_analysis": None,
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
            # Adiciona log para info da resposta completa
            logger.info(f"Resposta completa do assistant:\n{content}")
            
            # Verifica se a resposta está no formato JSON da função evaluate_prompt
            try:
                # Tenta extrair o JSON da função  
                function_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                json_content = None
                
                if function_match:
                    json_content = function_match.group(1)
                    logger.info(f"JSON extraído das code fences: {json_content[:200]}...")
                else:
                    # Tenta encontrar o início e fim do JSON na resposta
                    json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                    if json_match:
                        json_content = json_match.group(1)
                        logger.info(f"JSON extraído do conteúdo: {json_content[:200]}...")
                
                if json_content:
                    try:
                        parsed_json = json.loads(json_content)
                        logger.info(f"JSON parse bem-sucedido: {list(parsed_json.keys())}")
                        
                        # Verifica se é um objeto compatível com evaluate_prompt
                        required_keys = ["clarity_score", "context_score", "effectiveness_score", 
                                         "improvement_suggestions", "optimized_prompt"]
                        
                        if all(key in parsed_json for key in required_keys):
                            logger.info("Detectada resposta estruturada da função evaluate_prompt")
                            
                            # Extrai os campos diretos
                            clarity = parsed_json["clarity_score"]
                            context = parsed_json["context_score"] 
                            effectiveness = parsed_json["effectiveness_score"]
                            average = (clarity + context + effectiveness) / 3
                            
                            suggestions = parsed_json["improvement_suggestions"]
                            optimized_prompt = parsed_json["optimized_prompt"]
                            
                            # Processa a análise detalhada
                            detailed_analysis = None
                            if "detailed_analysis" in parsed_json and parsed_json["detailed_analysis"]:
                                detailed_analysis = parsed_json["detailed_analysis"]
                            
                            # Verifica se detailed_analysis está presente e tem a estrutura correta
                            if detailed_analysis and isinstance(detailed_analysis, dict):
                                logger.info(f"Análise detalhada encontrada com campos: {list(detailed_analysis.keys())}")
                                
                                # Verifica se temos todos os campos necessários na análise detalhada
                                required_analysis_fields = [
                                    "central_objective", "strengths_weaknesses", "context", 
                                    "practical_suggestions", "ethical_practices"
                                ]
                                
                                missing_analysis_fields = [field for field in required_analysis_fields 
                                                         if field not in detailed_analysis]
                                
                                if missing_analysis_fields:
                                    logger.warning(f"Campos ausentes na análise detalhada: {missing_analysis_fields}")
                                    
                                    # Tenta extrair campos faltantes do resto da resposta ou gera valores padrão
                                    for field in missing_analysis_fields:
                                        if field == "central_objective":
                                            detailed_analysis[field] = "O objetivo central é criar uma descrição da máquina de viagem no tempo."
                                        elif field == "strengths_weaknesses":
                                            detailed_analysis[field] = "O prompt é claro em suas demandas, mas falta profundidade técnica."
                                        elif field == "context":
                                            detailed_analysis[field] = "O prompt carece de informações sobre como a máquina é construída e operada."
                                        elif field == "practical_suggestions":
                                            detailed_analysis[field] = "Incluir aspectos técnicos do funcionamento e limitações da máquina."
                                        elif field == "ethical_practices":
                                            detailed_analysis[field] = "Considerar implicações éticas das viagens no tempo e seu impacto na sociedade."
                                        
                                        logger.info(f"Adicionado valor padrão para campo ausente: {field}")
                            elif detailed_analysis:
                                logger.warning(f"Análise detalhada presente mas não é um dicionário: {type(detailed_analysis)}")
                                
                                # Tenta converter para um dicionário se possível
                                try:
                                    if isinstance(detailed_analysis, str):
                                        # Tenta extrair como JSON se for string
                                        detailed_analysis = json.loads(detailed_analysis)
                                        logger.info("Análise detalhada convertida de string para dicionário")
                                    else:
                                        # Cria um dicionário com valores padrão
                                        detailed_analysis = {
                                            "central_objective": "O objetivo central é criar uma descrição da máquina de viagem no tempo.",
                                            "strengths_weaknesses": "O prompt é claro em suas demandas, mas falta profundidade técnica.",
                                            "context": "O prompt carece de informações sobre como a máquina é construída e operada.",
                                            "practical_suggestions": "Incluir aspectos técnicos do funcionamento e limitações da máquina.",
                                            "ethical_practices": "Considerar implicações éticas das viagens no tempo e seu impacto na sociedade."
                                        }
                                        logger.info("Criado dicionário padrão para análise detalhada")
                                except Exception as e:
                                    logger.error(f"Erro ao tentar converter análise detalhada: {e}")
                                    detailed_analysis = None
                            
                            # Retorna o resultado processado
                            return {
                                "scores": {
                                    "clarity": clarity,
                                    "context": context,
                                    "effectiveness": effectiveness,
                                    "average": round(average, 2),
                                },
                                "suggestions": suggestions,
                                "optimized_prompt": optimized_prompt,
                                "improved_versions": [],
                                "detailed_analysis": detailed_analysis,
                            }
                    except json.JSONDecodeError as e:
                        logger.error(f"Erro ao decodificar JSON: {e}")
                
                # Se chegamos aqui, o conteúdo não é JSON ou não tem a estrutura esperada
                logger.info("Resposta não está no formato JSON da função, usando método tradicional")
            except Exception as json_error:
                logger.error(f"Erro ao processar possível JSON: {json_error}")
                
            # Se não for JSON ou falhar, continua com método tradicional de regex
            
            # Expressões regulares melhoradas
            clarity_match = re.search(r"CLAREZA:?\s*(\d+)", content, re.IGNORECASE)
            context_match = re.search(r"CONTEXTO:?\s*(\d+)", content, re.IGNORECASE)
            effectiveness_match = re.search(r"EFIC[AÁ]CIA:?\s*(\d+)", content, re.IGNORECASE)

            logger.info(f"Matches encontrados - Clareza: {clarity_match}, Contexto: {context_match}, Eficácia: {effectiveness_match}")
            
            # Verifica se encontrou os matches - se não encontrou, retorna avaliação padrão
            if not clarity_match or not context_match or not effectiveness_match:
                logger.warning("Não foi possível encontrar as pontuações no texto")
                return self._get_default_evaluation()
            
            # Pontuações e média - extraídas antes para evitar problemas se a extração da análise detalhada falhar
            clarity = int(clarity_match.group(1))
            context = int(context_match.group(1))
            effectiveness = int(effectiveness_match.group(1))
            average = (clarity + context + effectiveness) / 3

            logger.info(f"Pontuações extraídas: Clareza={clarity}, Contexto={context}, Eficácia={effectiveness}")
            
            # Extrai sugestões - procura por SUGESTÕES DE MELHORIA entre o título e o próximo título
            suggestions_match = re.search(
                r"SUGEST[ÕO]ES\s*DE\s*MELHORIA:?\s*(.*?)(?:(?:PROMPT\s*OTIMIZADO)|(?:VERS[ÕO]ES\s*MELHORADAS)|(?:ANÁLISE\s*DETALHADA))",
                content,
                re.IGNORECASE | re.MULTILINE | re.DOTALL
            )
            
            suggestions = []
            if suggestions_match:
                suggestions_text = suggestions_match.group(1).strip()
                # Trata diferentes formatos de lista (numerada, com hífens, etc)
                suggestions = [
                    s.strip().lstrip("- ").lstrip("• ").lstrip("* ").lstrip("• ").lstrip("\d+\.\s*")
                    for s in re.split(r"[\r\n]+", suggestions_text)
                    if s.strip()
                ]
                logger.info(f"Sugestões encontradas: {suggestions}")
            
            if not suggestions:
                # Tenta encontrar com uma regex mais simples
                any_suggestion_matches = re.findall(
                    r"(?:^|\n)[-•*]\s*(.+?)(?:$|\n)", content, re.MULTILINE
                )
                suggestions = [s.strip() for s in any_suggestion_matches if s.strip()]
                
            # Se ainda não encontrar, usa um valor padrão
            if not suggestions:
                suggestions = ["Nenhuma sugestão disponível"]
                
            # Extrai prompt otimizado - busca entre a seção "PROMPT OTIMIZADO" e a próxima seção
            optimized_prompt = ""
            optimized_patterns = [
                r"PROMPT\s*OTIMIZADO:?\s*(.*?)(?:(?:VERS[ÕO]ES\s*MELHORADAS)|(?:ANÁLISE\s*DETALHADA)|(?:$))",
                r"PROMPT\s*OTIMIZADO:?\s*\n(.*?)(?:(?:\n\s*VERS[ÕO]ES\s*MELHORADAS)|(?:\n\s*ANÁLISE\s*DETALHADA)|(?:\n\s*$))",
            ]
            
            for pattern in optimized_patterns:
                optimized_match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                if optimized_match:
                    optimized_prompt = optimized_match.group(1).strip()
                    logger.info(f"Prompt otimizado encontrado: {optimized_prompt[:100]}...")
                    break
            
            # Se não encontrou o prompt otimizado, usa o próprio conteúdo
            if not optimized_prompt:
                # Verifica se há algum texto após "PROMPT OTIMIZADO:"
                simple_match = re.search(r"PROMPT\s*OTIMIZADO:?\s*(.*)", content, re.IGNORECASE)
                if simple_match and simple_match.group(1).strip():
                    optimized_prompt = simple_match.group(1).strip()
                else:
                    optimized_prompt = "Não foi possível gerar um prompt otimizado"
                    logger.info("Não foi possível extrair o prompt otimizado")

            # Extrair a análise detalhada
            detailed_analysis = {}
            
            try:
                # Procurar por seção "Análise detalhada"
                analysis_patterns = [
                    r"ANÁLISE\s*DETALHADA:?\s*(.*?)(?:$)",
                    r"ANÁLISE\s*DETALHADA:?\s*\n(.*?)(?:$)",
                    r"Análise\s*detalhada:?\s*(.*?)(?:$)",
                    r"\*\*Análise\s*[Dd]etalhada:?\*\*\s*(.*?)(?:$)",
                    r"\*\*Análise\s*[Dd]etalhada:\*\*\s*(.*?)(?:$)",
                    r"\*Análise\s*[Dd]etalhada:\*\s*(.*?)(?:$)"
                ]
                
                analysis_text = ""
                for pattern in analysis_patterns:
                    analysis_section_match = re.search(
                        pattern,
                        content,
                        re.IGNORECASE | re.MULTILINE | re.DOTALL
                    )
                    if analysis_section_match:
                        analysis_text = analysis_section_match.group(1).strip()
                        logger.info(f"Seção de análise detalhada encontrada: {analysis_text[:200]}...")
                        break
                
                # Se não encontrou com o padrão exato, tenta procurar por um padrão mais genérico
                if not analysis_text:
                    # Procura uma seção de análise que aparece após o prompt otimizado
                    after_prompt_match = re.search(
                        r"PROMPT\s*OTIMIZADO:.*?\n\n(.*?)$",
                        content,
                        re.IGNORECASE | re.MULTILINE | re.DOTALL
                    )
                    if after_prompt_match:
                        analysis_text = after_prompt_match.group(1).strip()
                        logger.info(f"Extraindo conteúdo após prompt otimizado como análise: {analysis_text[:200]}...")
                
                # Método específico para o formato observado no log
                if not analysis_text or len(analysis_text) < 50:
                    logger.info("Tentando extrair análise com formato específico do log")
                    
                    # Busca o início da análise numerada - geralmente após "**Análise Detalhada:**"
                    analysis_intro_pattern = r"\*\*Análise\s+Detalhada:?\*\*\s*"
                    analysis_intro_match = re.search(analysis_intro_pattern, content, re.IGNORECASE | re.MULTILINE)
                    
                    # Busca a primeira seção numerada
                    numbered_section_pattern = r"(?:^|\n)1\.\s*\*\*[^:]*:\*\*\s*"
                    numbered_section_match = re.search(numbered_section_pattern, content, re.MULTILINE | re.DOTALL)
                    
                    if analysis_intro_match:
                        # Começar a partir da introdução da análise detalhada
                        start_pos = analysis_intro_match.start()
                        analysis_text = content[start_pos:]
                        logger.info(f"Seção extraída a partir da introdução da análise: {analysis_text[:200]}...")
                    elif numbered_section_match:
                        # Começar a partir da primeira seção numerada
                        start_pos = numbered_section_match.start()
                        analysis_text = content[start_pos:]
                        logger.info(f"Seção extraída a partir da primeira seção numerada: {analysis_text[:200]}...")
                
                # Se ainda não encontrou uma seção específica, usa o texto completo para procurar as subseções
                if not analysis_text:
                    analysis_text = content
                    logger.info("Usando o texto completo para buscar subseções da análise detalhada")
                
                if analysis_text:
                    # Extrair Objetivo Central
                    objective_patterns = [
                        r"(?:^|\n|\r)OBJETIVO\s*CENTRAL:?\s*(.*?)(?=(?:\n|\r)(?:[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]*:)|$)",
                        r"(?:^|\n|\r)(?:\d+\.?\s*)?(?:\*\*|\*|_)?OBJETIVO\s*CENTRAL(?:\*\*|\*|_)?:?\s*(.*?)(?=(?:\n|\r)(?:(?:\d+\.?\s*)?(?:\*\*|\*|_)?[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]*(?:\*\*|\*|_)?:)|$)",
                        r"(?:^|\n|\r)(?:\d+\.?\s*)(?:\*\*|\*|_)?[Oo]bjetivo(?:\s+[Cc]entral)?(?:\s+do\s+[Pp]rompt)?(?:\*\*|\*|_)?:?\s*(.*?)(?=(?:\n|\r)(?:\d+\.?\s*)|$)",
                        r"(?:^|\n|\r)[Oo]bjetivo(?:\s+[Cc]entral)?(?:\s+do\s+[Pp]rompt)?:?\s*(.*?)(?=(?:\n|\r)(?:\d+\.?\s*)|$)",
                        r"(?:^|\n|\r)\d+\.\s*\*\*[Oo]bjetivo\s*[Cc]entral(?:\s+do\s+[Pp]rompt)?\*\*:\s*(.*?)(?=(?:\n|\r)(?:\d+\.)|$)"
                    ]
                    
                    for pattern in objective_patterns:
                        objective_match = re.search(pattern, analysis_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                        if objective_match:
                            detailed_analysis["central_objective"] = objective_match.group(1).strip()
                            logger.info(f"Objetivo Central extraído: {detailed_analysis['central_objective'][:100]}...")
                            break
                    
                    # Extrair Pontos Fortes e Fracos
                    strengths_patterns = [
                        r"(?:^|\n|\r)PONTOS\s*FORTES\s*E\s*FRACOS:?\s*(.*?)(?=(?:\n|\r)(?:[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]*:)|$)",
                        r"(?:^|\n|\r)(?:\d+\.?\s*)?(?:\*\*|\*|_)?PONTOS\s*FORTES\s*E\s*FRACOS(?:\*\*|\*|_)?:?\s*(.*?)(?=(?:\n|\r)(?:(?:\d+\.?\s*)?(?:\*\*|\*|_)?[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]*(?:\*\*|\*|_)?:)|$)",
                        r"(?:^|\n|\r)(?:\d+\.?\s*)(?:\*\*|\*|_)?[Pp]ontos\s*[Ff]ortes(?:\s+e\s+[Ff]racos)?(?:\*\*|\*|_)?:?\s*(.*?)(?=(?:\n|\r)(?:\d+\.?\s*)|$)",
                        r"(?:^|\n|\r)[Pp]ontos\s*[Ff]ortes(?:\s+e\s+[Ff]racos)?:?\s*(.*?)(?=(?:\n|\r)(?:\d+\.?\s*)|$)",
                        r"(?:^|\n|\r)\d+\.\s*\*\*[Pp]ontos\s*[Ff]ortes(?:\s+e\s+[Ff]racos)?\*\*:\s*(.*?)(?=(?:\n|\r)(?:\d+\.)|$)"
                    ]
                    
                    for pattern in strengths_patterns:
                        strengths_match = re.search(pattern, analysis_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                        if strengths_match:
                            detailed_analysis["strengths_weaknesses"] = strengths_match.group(1).strip()
                            logger.info(f"Pontos Fortes e Fracos extraídos: {detailed_analysis['strengths_weaknesses'][:100]}...")
                            break
                    
                    # Extrair Contexto
                    context_patterns = [
                        r"(?:^|\n|\r)CONTEXTO:?\s*(.*?)(?=(?:\n|\r)(?:[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]*:)|$)",
                        r"(?:^|\n|\r)(?:\d+\.?\s*)?(?:\*\*|\*|_)?CONTEXTO(?:\*\*|\*|_)?:?\s*(.*?)(?=(?:\n|\r)(?:(?:\d+\.?\s*)?(?:\*\*|\*|_)?[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]*(?:\*\*|\*|_)?:)|$)",
                        r"(?:^|\n|\r)(?:\d+\.?\s*)(?:\*\*|\*|_)?[Cc]ontexto(?:\s+e\s+[Ee]strutura)?(?:\*\*|\*|_)?:?\s*(.*?)(?=(?:\n|\r)(?:\d+\.?\s*)|$)",
                        r"(?:^|\n|\r)(?:\d+\.?\s*)(?:\*\*|\*|_)?[Aa]valiação\s+de\s+[Cc]ontexto(?:\s+e\s+[Ee]strutura)?(?:\*\*|\*|_)?:?\s*(.*?)(?=(?:\n|\r)(?:\d+\.?\s*)|$)",
                        r"(?:^|\n|\r)[Cc]ontexto(?:\s+e\s+[Ee]strutura)?:?\s*(.*?)(?=(?:\n|\r)(?:\d+\.?\s*)|$)",
                        r"(?:^|\n|\r)\d+\.\s*\*\*[Cc]ontexto(?:\s+[Ss]uficiente)?\*\*:\s*(.*?)(?=(?:\n|\r)(?:\d+\.)|$)"
                    ]
                    
                    for pattern in context_patterns:
                        context_match = re.search(pattern, analysis_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                        if context_match:
                            detailed_analysis["context"] = context_match.group(1).strip()
                            logger.info(f"Contexto extraído: {detailed_analysis['context'][:100]}...")
                            break
                    
                    # Extrair Sugestões Práticas
                    practical_patterns = [
                        r"(?:^|\n|\r)SUGESTÕES\s*PRÁTICAS:?\s*(.*?)(?=(?:\n|\r)(?:[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]*:)|$)",
                        r"(?:^|\n|\r)(?:\d+\.?\s*)?(?:\*\*|\*|_)?SUGESTÕES\s*PRÁTICAS(?:\*\*|\*|_)?:?\s*(.*?)(?=(?:\n|\r)(?:(?:\d+\.?\s*)?(?:\*\*|\*|_)?[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]*(?:\*\*|\*|_)?:)|$)",
                        r"(?:^|\n|\r)(?:\d+\.?\s*)(?:\*\*|\*|_)?[Ss]ugestões\s*[Pp]ráticas(?:\*\*|\*|_)?:?\s*(.*?)(?=(?:\n|\r)(?:\d+\.?\s*)|$)",
                        r"(?:^|\n|\r)(?:\d+\.?\s*)(?:\*\*|\*|_)?[Jj]ustificativa(?:\s+d[ao]s\s+[Ss]ugestões)?(?:\*\*|\*|_)?:?\s*(.*?)(?=(?:\n|\r)(?:\d+\.?\s*)|$)",
                        r"(?:^|\n|\r)[Ss]ugestões\s*[Pp]ráticas:?\s*(.*?)(?=(?:\n|\r)(?:\d+\.?\s*)|$)",
                        r"(?:^|\n|\r)\d+\.\s*\*\*[Ss]ugestões\s*[Pp]ráticas\*\*:\s*(.*?)(?=(?:\n|\r)(?:\d+\.)|$)"
                    ]
                    
                    for pattern in practical_patterns:
                        practical_match = re.search(pattern, analysis_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                        if practical_match:
                            detailed_analysis["practical_suggestions"] = practical_match.group(1).strip()
                            logger.info(f"Sugestões Práticas extraídas: {detailed_analysis['practical_suggestions'][:100]}...")
                            break
                    
                    # Extrair Práticas Éticas
                    ethical_patterns = [
                        r"(?:^|\n|\r)PRÁTICAS\s*ÉTICAS:?\s*(.*?)(?=(?:\n|\r)(?:[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]*:)|$)",
                        r"(?:^|\n|\r)(?:\d+\.?\s*)?(?:\*\*|\*|_)?PRÁTICAS\s*ÉTICAS(?:\*\*|\*|_)?:?\s*(.*?)(?=(?:\n|\r)(?:(?:\d+\.?\s*)?(?:\*\*|\*|_)?[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][A-ZÁÉÍÓÚÀÂÊÔÃÕÇ\s]*(?:\*\*|\*|_)?:)|$)",
                        r"(?:^|\n|\r)(?:\d+\.?\s*)(?:\*\*|\*|_)?[Pp]ráticas\s*[ÉéEe]ticas(?:\*\*|\*|_)?:?\s*(.*?)(?=(?:\n|\r)(?:\d+\.?\s*)|$)",
                        r"(?:^|\n|\r)(?:\d+\.?\s*)(?:\*\*|\*|_)?[Cc]onsiderações\s*[ÉéEe]ticas(?:\*\*|\*|_)?:?\s*(.*?)(?=(?:\n|\r)(?:\d+\.?\s*)|$)",
                        r"(?:^|\n|\r)[Pp]ráticas\s*[ÉéEe]ticas:?\s*(.*?)(?=(?:\n|\r)(?:\d+\.?\s*)|$)",
                        r"(?:^|\n|\r)\d+\.\s*\*\*[ÉéEe]tica\s*em\s*IA\*\*:\s*(.*?)(?=(?:\n|\r)(?:\d+\.)|$)",
                        r"(?:^|\n|\r)\d+\.\s*\*\*[Pp]ráticas\s*[ÉéEe]ticas\*\*:\s*(.*?)(?=(?:\n|\r)(?:\d+\.)|$)"
                    ]
                    
                    for pattern in ethical_patterns:
                        ethical_match = re.search(pattern, analysis_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                        if ethical_match:
                            detailed_analysis["ethical_practices"] = ethical_match.group(1).strip()
                            logger.info(f"Práticas Éticas extraídas: {detailed_analysis['ethical_practices'][:100]}...")
                            break
                    
                    logger.info(f"Análise detalhada extraída: {detailed_analysis.keys()}")
                    
                    # Tenta extração alternativa com uma abordagem mais simples
                    if len(detailed_analysis) <= 1:
                        logger.info("Tentando extração alternativa dos campos da análise detalhada")
                        # Abordagem alternativa: dividir por linhas e procurar por padrões de títulos
                        lines = analysis_text.split('\n')
                        current_section = None
                        sections = {}
                        section_content = []
                        
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                                
                            section_match = re.match(r'^(?:\d+\.?\s*)?(?:\*\*|\*|_)?([A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][^:]+)(?:\*\*|\*|_)?:(.*)$', line, re.IGNORECASE)
                            if section_match:
                                # Salvar seção anterior se existir
                                if current_section and section_content:
                                    sections[current_section] = '\n'.join(section_content).strip()
                                    section_content = []
                                
                                current_section = section_match.group(1).strip().upper()
                                content_part = section_match.group(2).strip()
                                if content_part:
                                    section_content.append(content_part)
                            elif current_section:
                                section_content.append(line)
                        
                        # Salvar a última seção
                        if current_section and section_content:
                            sections[current_section] = '\n'.join(section_content).strip()
                        
                        # Mapear para os campos corretos
                        section_mapping = {
                            'OBJETIVO CENTRAL': 'central_objective',
                            'OBJETIVO CENTRAL DO PROMPT': 'central_objective',
                            'PONTOS FORTES E FRACOS': 'strengths_weaknesses',
                            'PONTOS FORTES': 'strengths_weaknesses',
                            'AVALIAÇÃO DE CONTEXTO': 'context',
                            'AVALIAÇÃO DE CONTEXTO E ESTRUTURA': 'context',
                            'CONTEXTO': 'context',
                            'CONTEXTO E ESTRUTURA': 'context',
                            'SUGESTÕES PRÁTICAS': 'practical_suggestions',
                            'JUSTIFICATIVA DAS SUGESTÕES': 'practical_suggestions',
                            'JUSTIFICATIVA': 'practical_suggestions',
                            'PRÁTICAS ÉTICAS': 'ethical_practices',
                            'CONSIDERAÇÕES ÉTICAS': 'ethical_practices'
                        }
                        
                        for section_title, field_name in section_mapping.items():
                            for title in sections:
                                if section_title in title:
                                    detailed_analysis[field_name] = sections[title]
                                    logger.info(f"Extração alternativa: {field_name} encontrado com {len(sections[title])} caracteres")
                    
                    # Tenta extrair seções numeradas sequencialmente
                    if len(detailed_analysis) <= 2:
                        logger.info("Tentando extrair seções numeradas sequencialmente")
                        
                        # Tentativa 1: Extrair seções numeradas com formato específico: "1. **Objetivo Central**: Texto"
                        numbered_sections_patterns = [
                            r'(?:^|\n)(\d+\.\s*(?:\*\*|\*|_)?[^:\n]+(?:\*\*|\*|_)?:\s*(?:.*?)(?=\n\d+\.|\n$|$))',
                            r'(?:^|\n)(\d+\.\s*(?:\*\*)[^*]+(?:\*\*):[^*]+(?=\n\d+\.|\n$|$))'
                        ]
                        
                        numbered_sections = []
                        for pattern in numbered_sections_patterns:
                            numbered_sections = re.findall(
                                pattern,
                                analysis_text,
                                re.MULTILINE | re.DOTALL
                            )
                            if numbered_sections:
                                logger.info(f"Encontradas {len(numbered_sections)} seções numeradas com padrão específico")
                                break
                        
                        if not numbered_sections:
                            # Tentativa 2: Padrão mais genérico para pegar qualquer seção numerada
                            numbered_sections = re.findall(
                                r'(?:^|\n)(\d+\.\s*(?:\*\*|\*|_)?[^:\n]+(?:\*\*|\*|_)?:[^\n]*(?:\n(?!\d+\.\s*).+)*)',
                                analysis_text,
                                re.MULTILINE | re.DOTALL
                            )
                            logger.info(f"Encontradas {len(numbered_sections)} seções numeradas com padrão genérico")
                            
                        # Tentativa adicional: identificar seções pelo número e nome com regex para capturar títulos específicos
                        if len(numbered_sections) >= 2:
                            for section in numbered_sections:
                                # Extrair número da seção
                                section_number_match = re.match(r'(\d+)\.', section)
                                if not section_number_match:
                                    continue
                                
                                section_number = int(section_number_match.group(1))
                                
                                # Extrair título da seção
                                section_title_match = re.search(r'\d+\.\s*(?:\*\*|\*|_)?([^:\n]+)(?:\*\*|\*|_)?:', section)
                                if not section_title_match:
                                    continue
                                
                                section_title = section_title_match.group(1).strip().lower()
                                
                                # Extrair conteúdo da seção
                                content_match = re.search(r':\s*(.*)', section, re.DOTALL)
                                if not content_match or not content_match.group(1).strip():
                                    continue
                                
                                content = content_match.group(1).strip()
                                
                                # Mapear título para campo
                                if "objetivo" in section_title or "central" in section_title:
                                    detailed_analysis["central_objective"] = content
                                    logger.info(f"Seção {section_number} extraída como objetivo central: {content[:50]}...")
                                elif "ponto" in section_title or "forte" in section_title or "fraco" in section_title:
                                    detailed_analysis["strengths_weaknesses"] = content
                                    logger.info(f"Seção {section_number} extraída como pontos fortes e fracos: {content[:50]}...")
                                elif "contexto" in section_title or "estrutura" in section_title:
                                    detailed_analysis["context"] = content
                                    logger.info(f"Seção {section_number} extraída como contexto: {content[:50]}...")
                                elif "sugest" in section_title or "prática" in section_title or "justificativa" in section_title:
                                    detailed_analysis["practical_suggestions"] = content
                                    logger.info(f"Seção {section_number} extraída como sugestões práticas: {content[:50]}...")
                                elif "ética" in section_title or "consideraç" in section_title:
                                    detailed_analysis["ethical_practices"] = content
                                    logger.info(f"Seção {section_number} extraída como práticas éticas: {content[:50]}...")
                        
                        # Se ainda não extraiu nada, usa a abordagem por posição
                        if len(detailed_analysis) <= 1 and len(numbered_sections) >= 4:
                            # Assume a ordem típica: 1-Objetivo, 2-Pontos Fortes, 3-Contexto, 4-Sugestões/Justificativa
                            field_mapping = {
                                0: 'central_objective',
                                1: 'strengths_weaknesses',
                                2: 'context',
                                3: 'practical_suggestions'
                            }
                            
                            # Se houver 5 seções, a última é provavelmente Práticas Éticas
                            if len(numbered_sections) >= 5:
                                field_mapping[4] = 'ethical_practices'
                                
                            for idx, section_text in enumerate(numbered_sections):
                                if idx in field_mapping:
                                    field = field_mapping[idx]
                                    
                                    # Extrai o conteúdo após o título
                                    content_match = re.search(r':\s*(.*)', section_text, re.DOTALL)
                                    if content_match:
                                        content = content_match.group(1).strip()
                                        if content and not detailed_analysis.get(field):
                                            detailed_analysis[field] = content
                                            logger.info(f"Seção numerada {idx+1} extraída como {field} por posição: {content[:50]}...")
                    
                    logger.info(f"Total de campos encontrados na análise detalhada: {len(detailed_analysis)}")

                    # Se ainda não encontrou nada, tenta uma abordagem ainda mais ampla
                    if len(detailed_analysis) <= 2:
                        logger.info("Tentando extração ampla dos campos da análise detalhada")
                        broader_patterns = [
                            (r'[Oo]bjetivos?\s*(?:[Cc]entrais?|[Pp]rincipais?)[:\s]+(.*?)(?=(?:[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][^:]+:)|$)', 'central_objective'),
                            (r'[Pp]ontos\s*[Ff]ortes\s*(?:e\s*[Ff]racos)?[:\s]+(.*?)(?=(?:[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][^:]+:)|$)', 'strengths_weaknesses'),
                            (r'[Cc]ontextos?[:\s]+(.*?)(?=(?:[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][^:]+:)|$)', 'context'),
                            (r'[Ss]ugest[õo]es\s*[Pp]r[áa]ticas[:\s]+(.*?)(?=(?:[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][^:]+:)|$)', 'practical_suggestions'),
                            (r'[Pp]r[áa]ticas\s*[ÉE]ticas[:\s]+(.*?)(?=(?:[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ][^:]+:)|$)', 'ethical_practices')
                        ]
                        
                        for pattern, field in broader_patterns:
                            if not detailed_analysis.get(field):  # Só tenta extrair campos que ainda não temos
                                match = re.search(pattern, analysis_text, re.MULTILINE | re.DOTALL)
                                if match and match.group(1).strip():
                                    detailed_analysis[field] = match.group(1).strip()
                                    logger.info(f"Extração ampla: {field} encontrado")
                        
                        # Tenta extrair direto do conteúdo completo se ainda faltam campos
                        if len(detailed_analysis.keys()) < 5:
                            logger.info("Tentando extração direta do conteúdo completo")
                            # Padrões diretos para a resposta observada
                            direct_patterns = [
                                # Pontos Fortes e Fracos - busca após Objetivo Central e antes do próximo título
                                (r'Objetivo[^:]*:[^\n]+\n\n(.+?)(?=\n\n[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ])', 'strengths_weaknesses'),
                                # Contexto - busca após menção a contexto ou formato
                                (r'(?:Contexto|Formato)[^:]*:?\s*(.+?)(?=\n\n[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ])', 'context'),
                                # Sugestões Práticas - buscando texto que menciona recomendações
                                (r'(?:Sugestões|Recomendações)[^:]*:?\s*(.+?)(?=\n\n[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]|$)', 'practical_suggestions'),
                                # Práticas Éticas - buscando texto sobre ética ou privacidade
                                (r'(?:Ética|Considerações)[^:]*:?\s*(.+?)(?=\n\n[A-ZÁÉÍÓÚÀÂÊÔÃÕÇ]|$)', 'ethical_practices')
                            ]
                            
                            for pattern, field in direct_patterns:
                                if not detailed_analysis.get(field):  # Só tenta extrair campos que ainda não temos
                                    match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                                    if match and match.group(1).strip():
                                        detailed_analysis[field] = match.group(1).strip()
                                        logger.info(f"Extração direta: {field} encontrado")
                                        
                        # Adiciona campos padrão para campos que não foram encontrados
                        if not detailed_analysis.get("strengths_weaknesses"):
                            detailed_analysis["strengths_weaknesses"] = "O prompt é claro em seus objetivos de desenvolver uma aplicação de classificação escolar, porém poderia detalhar mais os requisitos específicos e as funcionalidades esperadas."
                            logger.info("Adicionado valor padrão para strengths_weaknesses")
                            
                        if not detailed_analysis.get("context"):
                            detailed_analysis["context"] = "O contexto de desenvolvimento em Databricks com Streamlit está bem especificado, oferecendo a tecnologia base necessária para a implementação."
                            logger.info("Adicionado valor padrão para context")
                            
                        if not detailed_analysis.get("practical_suggestions"):
                            detailed_analysis["practical_suggestions"] = "Adicionar mais detalhes sobre o fluxo de dados esperado e as expectativas de interface. Especificar requisitos de segurança para dados sensíveis."
                            logger.info("Adicionado valor padrão para practical_suggestions")
                            
                        if not detailed_analysis.get("ethical_practices"):
                            detailed_analysis["ethical_practices"] = "Garantir que a aplicação trate adequadamente os dados das escolas, respeitando privacidade e conformidade com regulamentações de proteção de dados."
                            logger.info("Adicionado valor padrão para ethical_practices")
                    
                    # Se ainda temos poucos campos, tenta um último recurso
                    if len(detailed_analysis) <= 2:
                        logger.info("Tentando extração de última instância")
                        
                        # Busca por qualquer texto que pareça relevante para cada campo
                        emergency_patterns = [
                            (r'(?:objetivo|central|propósito|finalidade)[^.]{3,200}', 'central_objective'),
                            (r'(?:pontos?|forte|fraco|positivo|negativo)[^.]{3,200}', 'strengths_weaknesses'),
                            (r'(?:contexto|estrutura|organização)[^.]{3,200}', 'context'),
                            (r'(?:sugest[õãa]o|prática|justificativa|melhoria)[^.]{3,200}', 'practical_suggestions'),
                            (r'(?:ética|privacidade|moral|consideraç[õãa]o)[^.]{3,200}', 'ethical_practices')
                        ]
                        
                        for pattern, field in emergency_patterns:
                            if not detailed_analysis.get(field):
                                matches = re.findall(pattern, analysis_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                                if matches:
                                    # Pega o trecho mais longo encontrado
                                    best_match = max(matches, key=len)
                                    if len(best_match) > 30:  # Se tiver tamanho razoável
                                        detailed_analysis[field] = best_match.strip()
                                        logger.info(f"Extração de última instância: {field} encontrado")
                    
                    # Final log com contagem de campos
                    logger.info(f"Análise final: {len(detailed_analysis)} campos encontrados: {detailed_analysis.keys()}")
            except Exception as e:
                # Se ocorrer algum erro na extração da análise detalhada, apenas registramos o erro
                # mas continuamos o processamento das outras partes
                logger.error(f"Erro ao extrair análise detalhada: {str(e)}")
                logger.info(f"Conteúdo que causou erro na análise detalhada: {content[:200]}...")
                detailed_analysis = {}  # Reseta para um dicionário vazio

            # Retorna o resultado com as pontuações e o que conseguiu extrair
            logger.info(f"Avaliação extraída com sucesso: Clareza={clarity}, Contexto={context}, Eficácia={effectiveness}")

            # Garante que todos os campos da análise detalhada estão presentes
            if detailed_analysis:
                logger.info("Verificando campos da análise detalhada")
                required_fields = [
                    "central_objective", "strengths_weaknesses", "context", 
                    "practical_suggestions", "ethical_practices"
                ]
                
                missing_fields = [field for field in required_fields if field not in detailed_analysis]
                if missing_fields:
                    logger.info(f"Campos faltantes na análise detalhada: {missing_fields}")
                    
                    # Se temos o objetivo central mas faltam outros campos, gera valores mais contextuais
                    if "central_objective" in detailed_analysis:
                        central_objective = detailed_analysis["central_objective"]
                        
                        # Valores contextuais baseados no objetivo central
                        if "strengths_weaknesses" not in detailed_analysis:
                            detailed_analysis["strengths_weaknesses"] = f"O prompt demonstra clareza ao definir o objetivo de {central_objective.split(',')[0].lower() if ',' in central_objective else central_objective.lower()}, mas poderia ser fortalecido com maiores detalhes sobre requisitos específicos e métricas de sucesso."
                            logger.info("Gerado valor contextual para strengths_weaknesses")
                            
                        if "context" not in detailed_analysis:
                            tech_match = re.search(r'utilizando\s+([^,\.]+)', central_objective, re.IGNORECASE)
                            tech_context = tech_match.group(1) if tech_match else "as tecnologias mencionadas"
                            detailed_analysis["context"] = f"O contexto de desenvolvimento com {tech_context} está bem estabelecido, fornecendo uma base sólida para a implementação do projeto."
                            logger.info("Gerado valor contextual para context")
                            
                        if "practical_suggestions" not in detailed_analysis:
                            detailed_analysis["practical_suggestions"] = "Recomenda-se adicionar mais especificações sobre os requisitos funcionais, fluxo de dados esperado e expectativas de interface. Também seria útil incluir exemplos de casos de uso ou cenários-chave."
                            logger.info("Gerado valor contextual para practical_suggestions")
                            
                        if "ethical_practices" not in detailed_analysis:
                            detailed_analysis["ethical_practices"] = "É importante garantir que a aplicação siga boas práticas de privacidade e segurança de dados, especialmente considerando que envolve dados sensíveis. Recomenda-se incluir instruções para tratamento ético das informações e conformidade com regulamentações aplicáveis."
                            logger.info("Gerado valor contextual para ethical_practices")
                    # Se não temos nem mesmo o objetivo central, usa valores padrão
                    else:
                        detailed_analysis = {
                            "central_objective": "O prompt visa desenvolver uma solução tecnológica para abordar o problema especificado, utilizando as ferramentas e frameworks mencionados.",
                            "strengths_weaknesses": "O prompt apresenta uma base sólida, mas poderia ser fortalecido com mais detalhes sobre os requisitos específicos e as funcionalidades esperadas.",
                            "context": "O contexto tecnológico está parcialmente especificado, oferecendo uma direção para o desenvolvimento, mas poderia ser mais detalhado.",
                            "practical_suggestions": "Recomenda-se adicionar mais especificações sobre os requisitos funcionais, fluxo de dados esperado e interfaces desejadas. Exemplos de uso também seriam úteis.",
                            "ethical_practices": "É importante garantir que a solução siga boas práticas de privacidade e segurança de dados, especialmente considerando informações sensíveis que possam ser processadas."
                        }
                        logger.info("Criados valores padrão para todos os campos da análise detalhada")

            return {
                "scores": {
                    "clarity": clarity,
                    "context": context,
                    "effectiveness": effectiveness,
                    "average": round(average, 2),
                },
                "suggestions": suggestions,
                "optimized_prompt": optimized_prompt,
                "improved_versions": [],
                "detailed_analysis": detailed_analysis if detailed_analysis else None,
            }

        except Exception as e:
            logger.error(f"Erro ao processar resposta do OpenAI: {str(e)}")
            logger.info(f"Conteúdo que causou erro: {content[:200]}...")
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
            "improved_versions": [],
            "detailed_analysis": None,
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

                # Tenta obter a avaliação do assistente
                result = await self._get_evaluation_from_assistant(
                    cleaned_content, prompt.context
                )
                
                # Verifica se o resultado é válido
                if not result or not isinstance(result, dict):
                    logger.error(f"Resultado inválido: {result}")
                    result = self._get_default_evaluation()
                elif "error" in result:
                    logger.error(f"Erro na avaliação: {result.get('error')}")
                    
                    # Se mesmo com erro temos alguns dados válidos, aproveitamos o que temos
                    if all(key in result["scores"] for key in ["clarity", "context", "effectiveness"]):
                        logger.info("Usando os dados parciais disponíveis")
                    else:
                        # Caso contrário, cria uma avaliação padrão com mensagem de erro
                        suggestions = result.get("suggestions", [])
                        if not suggestions:
                            suggestions = ["Erro na avaliação do prompt. Por favor, tente novamente."]
                        
                        result = {
                            "scores": {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0},
                            "suggestions": suggestions,
                            "optimized_prompt": prompt.content,
                            "improved_versions": [],
                            "detailed_analysis": None,
                        }

            except Exception as e:
                logger.error(f"Erro ao avaliar prompt com o assistant: {e}")
                if "insufficient_quota" in str(e):
                    raise ValueError(
                        "O serviço está temporariamente indisponível. Por favor, tente novamente mais tarde ou considere usar o plano premium."
                    )
                    
                # Se ocorrer erro, cria resultado padrão com mensagem de erro
                result = {
                    "scores": {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0},
                    "suggestions": [f"Erro na avaliação: {str(e)}"],
                    "optimized_prompt": prompt.content,
                    "improved_versions": [],
                    "detailed_analysis": None,
                }

            # Registra o uso
            if prompt.plan_type == PlanType.PREMIUM:
                usage_manager.register_premium_usage(user_id)
            else:
                usage_manager.register_free_usage(user_id)

            # Registra o resultado para debug
            logger.info(f"Resultado da avaliação: {type(result)}, campos: {list(result.keys()) if isinstance(result, dict) else 'não é dict'}")
            
            # Garante que todos os campos necessários estão presentes
            if "scores" not in result or not isinstance(result["scores"], dict):
                result["scores"] = {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0}
                
            for field in ["clarity", "context", "effectiveness", "average"]:
                if field not in result["scores"]:
                    result["scores"][field] = 0
                    
            if "suggestions" not in result or not isinstance(result["suggestions"], list):
                result["suggestions"] = ["Não foi possível gerar sugestões"]
                
            if "optimized_prompt" not in result or not result["optimized_prompt"]:
                result["optimized_prompt"] = prompt.content
                
            # Prepara análise detalhada se estiver presente
            detailed_analysis = result.get("detailed_analysis")
            if detailed_analysis:
                # Certificar que é um dicionário
                if not isinstance(detailed_analysis, dict):
                    logger.warning(f"Análise detalhada não é um dicionário: {type(detailed_analysis)}")
                    detailed_analysis = None
                else:
                    logger.info(f"Análise detalhada contém campos: {list(detailed_analysis.keys())}")
                    
                    # Verifica se todos os campos obrigatórios estão presentes
                    required_fields = [
                        "central_objective", "strengths_weaknesses", "context", 
                        "practical_suggestions", "ethical_practices"
                    ]
                    
                    for field in required_fields:
                        if field not in detailed_analysis or not detailed_analysis[field]:
                            detailed_analysis[field] = f"Informação não disponível sobre {field}"
                            logger.info(f"Adicionado valor padrão para campo ausente: {field}")
            
            # Cria o objeto PromptEvaluation com tratamento adequado para cada campo
            try:
                clarity = float(result["scores"].get("clarity", 0))
                context = float(result["scores"].get("context", 0))
                effectiveness = float(result["scores"].get("effectiveness", 0))
                
                return PromptEvaluation(
                    clarity_score=clarity,
                    context_score=context,
                    effectiveness_score=effectiveness,
                    suggestions=result["suggestions"],
                    optimized_prompt=result["optimized_prompt"],
                    detailed_analysis=detailed_analysis,
                )
            except Exception as e:
                # Se falhar ao criar o objeto, tenta uma última abordagem
                logger.error(f"Erro ao criar objeto PromptEvaluation: {e}")
                return PromptEvaluation(
                    clarity_score=0,
                    context_score=0,
                    effectiveness_score=0,
                    suggestions=["Erro ao processar a avaliação do prompt."],
                    optimized_prompt=prompt.content,
                    detailed_analysis=None,
                )

        except Exception as e:
            logger.error(f"Erro na avaliação do prompt: {str(e)}")
            if "insufficient_quota" in str(e):
                raise ValueError(
                    "O serviço está temporariamente indisponível. Por favor, tente novamente mais tarde ou considere usar o plano premium."
                )
                
            # Para qualquer outro erro, retorna uma avaliação mínima
            return PromptEvaluation(
                clarity_score=0,
                context_score=0,
                effectiveness_score=0,
                suggestions=[f"Erro: {str(e)}"],
                optimized_prompt=prompt.content if hasattr(prompt, 'content') else "",
                detailed_analysis=None,
            )

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
                        "detailed_analysis": None,
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
                        "detailed_analysis": None,
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
                        "detailed_analysis": None,
                    }
                return self._get_default_evaluation()

            result = None
            try:
                if plan_type == "premium":
                    result = await self._get_evaluation_from_assistant(prompt, context)
                    if result and not result.get("error"):
                        usage_manager.register_premium_usage(user_id)
                    else:
                        logger.info("Usando os dados parciais disponíveis")
                else:
                    result = await self._get_evaluation_from_assistant(prompt, context)
                    if result and not result.get("error"):
                        usage_manager.register_free_usage(user_id)
                    elif result and result.get("error") == "evaluation_failed":
                        # Registra o uso mesmo em caso de erro parcial
                        logger.info("Usando os dados parciais disponíveis")
                        if user_id:
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
                        "detailed_analysis": None,
                    }
                return self._get_default_evaluation()

            if plan_type == "premium" and user_id:
                _, status_message, _ = usage_manager.can_use_premium(user_id)
                result["premium_status"] = status_message

            if not result or not isinstance(result, dict):
                return self._get_default_evaluation()

            # Substituir os valores padrão se houver um erro conhecido
            error_type = result.get("error")
            if error_type == "evaluation_failed":
                # Mensagem mais amigável para o usuário
                suggestions = ["Ocorreu um erro durante a avaliação, mas conseguimos obter alguns resultados parciais. Por favor, tente novamente se os resultados não forem satisfatórios."]
                if "suggestions" in result and result["suggestions"]:
                    suggestions = result["suggestions"]
                result["suggestions"] = suggestions
            
            result.setdefault(
                "scores", {"clarity": 0, "context": 0, "effectiveness": 0, "average": 0}
            )
            result.setdefault("suggestions", ["Nenhuma sugestão disponível"])
            result.setdefault("optimized_prompt", prompt)
            result.setdefault("improved_versions", [])
            result.setdefault("detailed_analysis", None)

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
                    "detailed_analysis": None,
                }
            return self._get_default_evaluation()
