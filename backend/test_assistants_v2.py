"""
Script para testar a integração com o OpenAI Assistant API v2.
"""

import os
import time
import asyncio
import requests
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações
API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID_PREMIUM")

# API URL base
BASE_URL = "https://api.openai.com/v1"

# Headers comuns para todas as requisições
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "OpenAI-Beta": "assistants=v2"
}

async def test_assistant_v2():
    """Testa a integração com o OpenAI Assistant API v2."""
    print("Iniciando teste do OpenAI Assistant v2...")
    
    # Inicializa o cliente
    print(f"Usando API Key: {API_KEY[:10]}...")
    print(f"Usando Assistant ID: {ASSISTANT_ID}")
    
    # Cria uma thread
    print("Criando thread...")
    response = requests.post(
        f"{BASE_URL}/threads",
        headers=headers,
        json={}
    )
    
    if response.status_code != 200:
        print(f"Erro ao criar thread: {response.status_code}")
        print(response.json())
        return
        
    thread_data = response.json()
    thread_id = thread_data["id"]
    print(f"Thread criada com ID: {thread_id}")
    
    # Adiciona uma mensagem
    print("Adicionando mensagem...")
    response = requests.post(
        f"{BASE_URL}/threads/{thread_id}/messages",
        headers=headers,
        json={
            "role": "user",
            "content": "Por favor, avalie o seguinte prompt: 'Explique o funcionamento básico de uma API REST para um iniciante em programação.'"
        }
    )
    
    if response.status_code != 200:
        print(f"Erro ao adicionar mensagem: {response.status_code}")
        print(response.json())
        return
        
    message_data = response.json()
    message_id = message_data["id"]
    print(f"Mensagem adicionada: {message_id}")
    
    # Inicia a execução
    print(f"Executando assistant {ASSISTANT_ID}...")
    response = requests.post(
        f"{BASE_URL}/threads/{thread_id}/runs",
        headers=headers,
        json={
            "assistant_id": ASSISTANT_ID
        }
    )
    
    if response.status_code != 200:
        print(f"Erro ao executar assistant: {response.status_code}")
        print(response.json())
        return
        
    run_data = response.json()
    run_id = run_data["id"]
    print(f"Execução iniciada com ID: {run_id}")
    
    # Monitora a execução
    print("Aguardando conclusão...")
    run_status = run_data["status"]
    
    while run_status not in ["completed", "failed", "cancelled", "expired"]:
        print(f"Status atual: {run_status}")
        await asyncio.sleep(2)
        
        response = requests.get(
            f"{BASE_URL}/threads/{thread_id}/runs/{run_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"Erro ao verificar status: {response.status_code}")
            print(response.json())
            break
            
        run_data = response.json()
        run_status = run_data["status"]
    
    # Verifica o resultado
    print(f"Execução concluída com status: {run_status}")
    
    if run_status == "completed":
        # Obtém as mensagens
        print("Obtendo mensagens...")
        response = requests.get(
            f"{BASE_URL}/threads/{thread_id}/messages",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"Erro ao obter mensagens: {response.status_code}")
            print(response.json())
            return
            
        messages_data = response.json()
        
        # Exibe a resposta
        print("Resposta do assistant:")
        for message in messages_data["data"]:
            if message["role"] == "assistant":
                print("\n--- INÍCIO DA RESPOSTA ---")
                for content_item in message["content"]:
                    if content_item["type"] == "text":
                        print(content_item["text"]["value"])
                print("--- FIM DA RESPOSTA ---\n")
    else:
        print(f"Falha na execução: {run_status}")

if __name__ == "__main__":
    asyncio.run(test_assistant_v2()) 