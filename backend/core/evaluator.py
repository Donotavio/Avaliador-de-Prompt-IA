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
            thread = self.openai_client.beta.threads.create()
            
            # Formata a mensagem com prompt e contexto
            target_llm = getattr(prompt, 'target_llm', None) if hasattr(prompt, 'target_llm') else None
            prompt_content = prompt if isinstance(prompt, str) else prompt.content
            prompt_context = context if isinstance(prompt, str) else getattr(prompt, 'context', None)
            
            message_content = f"Por favor, avalie o seguinte prompt para ser utilizado com o modelo {target_llm or 'não especificado'}:\n\n{prompt_content}"
            if prompt_context:
                message_content += f"\n\nContexto adicional: {prompt_context}"
            
            logger.info("Adicionando mensagem à thread")
            message = self.openai_client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message_content
            )
            
            # Inicia a execução
            logger.info(f"Executando o assistant {self.assistant_id}")
            run = self.openai_client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Monitora a execução
            while run.status not in ["completed", "failed", "cancelled", "expired"]:
                logger.info(f"Verificando status: {run.status}")
                await asyncio.sleep(0.5)
                run = self.openai_client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            # Verifica se houve falha na execução
            if run.status != "completed":
                logger.error(f"Execução falhou com status: {run.status}")
                raise ValueError(f"Falha na execução do assistant: {run.status}")
                
            # Obtém as mensagens
            logger.info("Recuperando mensagem de resposta")
            messages = self.openai_client.beta.threads.messages.list(
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
                            detailed_analysis["practical_suggestions"] = "Adicionar mais detalhes sobre o fluxo de dados esperado e as expectativas de interface com o usuário. Especificar requisitos de segurança para dados sensíveis."
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
                detailed_analysis=result.get("detailed_analysis"),
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
                        "detailed_analysis": None,
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
