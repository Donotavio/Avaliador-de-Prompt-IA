"""
Patch para monitorar pedidos à OpenAI.
Este arquivo deve ser importado antes de importar a biblioteca OpenAI.

Exemplo de uso:
    import openai_patch
    from openai import OpenAI

Patch para compatibilidade com a biblioteca OpenAI.

Este módulo aplica um patch para tornar a biblioteca OpenAI compatível com a versão mais recente.
"""

import os
from dotenv import load_dotenv
import httpx
from functools import wraps
from typing import Any, Callable

# Carrega variáveis de ambiente
load_dotenv()

# Monkey patching para o OpenAI
try:
    # Importa os módulos necessários
    from openai._base_client import APIRequestor
    from openai._client import OpenAI as OriginalOpenAI
    import openai.resources.beta as beta_resources
    
    # Guarda a função original do httpx para fazer requisições
    original_request = httpx.Client.request
    
    # Modifica a função de requisição do httpx para incluir o cabeçalho OpenAI-Beta
    @wraps(original_request)
    def patched_httpx_request(self, *args, **kwargs):
        # Adiciona o cabeçalho OpenAI-Beta a todas as requisições que contêm openai.com
        headers = kwargs.get("headers", {})
        url = kwargs.get("url", "")
        
        if "openai.com" in str(url) and "api.openai.com/v1/threads" in str(url):
            if "OpenAI-Beta" not in headers:
                headers["OpenAI-Beta"] = "assistants=v2"
                kwargs["headers"] = headers
                print(f"[DEBUG] Adicionado cabeçalho OpenAI-Beta a requisição para {url}")
        
        # Faz a requisição original com os cabeçalhos atualizados
        return original_request(self, *args, **kwargs)
    
    # Aplica o patch ao httpx.Client.request
    httpx.Client.request = patched_httpx_request
    
    # Patch para o método _request do APIRequestor
    original_api_request = APIRequestor._request
    
    @wraps(original_api_request)
    def patched_request(self, *args, **kwargs):
        """Versão do _request que garante cabeçalho OpenAI-Beta e mostra informações de debug."""
        # Garante que o cabeçalho OpenAI-Beta esteja presente para todas as requisições
        headers = kwargs.get("headers", {})
        url = kwargs.get("url", "")
        
        if "threads" in str(url) and "OpenAI-Beta" not in headers:
            headers["OpenAI-Beta"] = "assistants=v2"
            kwargs["headers"] = headers
            print(f"[DEBUG] Adicionado cabeçalho OpenAI-Beta v2 à requisição de threads")
            
        print("\n=== OPENAI REQUEST ===")
        print(f"URL: {kwargs.get('url', 'N/A')}")
        print(f"Method: {kwargs.get('method', 'N/A')}")
        print(f"Headers: {kwargs.get('headers', {})}")
        print(f"Params: {kwargs.get('params', {})}")
        print(f"JSON: {kwargs.get('json', {})}")
        print("=====================\n")
        
        try:
            return original_api_request(self, *args, **kwargs)
        except Exception as e:
            print(f"\n=== OPENAI ERROR ===")
            print(f"Error: {str(e)}")
            print("===================\n")
            raise
    
    # Substitui a função original pela versão modificada
    APIRequestor._request = patched_request
    
    # Sobrescreve a classe OpenAI para sempre usar o cabeçalho correto
    class PatchedOpenAI(OriginalOpenAI):
        def __init__(self, *args, **kwargs):
            # Garante que o cabeçalho de Beta esteja presente
            headers = kwargs.get("default_headers", {}) or {}
            headers["OpenAI-Beta"] = "assistants=v2"
            kwargs["default_headers"] = headers
            
            # Certifica-se de que há uma API key, usando a do ambiente se não for fornecida
            if not kwargs.get("api_key"):
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    kwargs["api_key"] = api_key
            
            super().__init__(*args, **kwargs)
    
    # Substitui a classe original no módulo
    import sys
    sys.modules["openai"].OpenAI = PatchedOpenAI
    
    print("OpenAI API monitor e patch para assistants=v2 ativados com sucesso!")
    
except ImportError:
    print("OpenAI não foi importado ainda. O patch só funcionará se este módulo for importado primeiro.")
except Exception as e:
    print(f"Erro ao aplicar patch na OpenAI: {str(e)}")

def apply_patch():
    """
    Função que aplica o patch para compatibilidade com a biblioteca OpenAI.
    Isso não é mais necessário com a versão mais recente da OpenAI, mas
    mantemos a função para evitar quebras no código existente.
    """
    print("OpenAI patch aplicado (não necessário para as versões mais recentes)")
    return True

# Aplicar o patch automaticamente ao importar o módulo
apply_patch() 