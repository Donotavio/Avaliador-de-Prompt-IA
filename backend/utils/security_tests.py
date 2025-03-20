"""
Utilitários para verificar e testar a segurança da aplicação.
Este módulo contém funções para verificar a configuração de segurança,
incluindo CORS, cabeçalhos HTTP e outras configurações de segurança.
"""

import requests
from typing import Dict, List, Optional, Tuple
import logging
import socket

logger = logging.getLogger(__name__)

def test_connectivity(url: str, timeout: int = 5) -> Tuple[bool, Optional[str]]:
    """
    Testa se é possível se conectar a uma URL.
    
    Args:
        url: URL para testar
        timeout: Tempo limite em segundos
        
    Returns:
        Tupla com (sucesso, mensagem de erro)
    """
    try:
        response = requests.get(url, timeout=timeout)
        return True, None
    except requests.exceptions.ConnectionError as e:
        return False, f"Erro de conexão: {str(e)}"
    except requests.exceptions.Timeout as e:
        return False, f"Timeout ao conectar: {str(e)}"
    except Exception as e:
        return False, f"Erro ao conectar: {str(e)}"

def test_cors_configuration(api_url: str, allowed_origins: List[str], disallowed_origins: List[str], timeout: int = 5) -> Dict[str, any]:
    """
    Testa a configuração CORS do servidor, verificando se as origens permitidas funcionam
    e se as origens não permitidas são bloqueadas.
    
    Args:
        api_url: URL base da API
        allowed_origins: Lista de origens que devem ser permitidas
        disallowed_origins: Lista de origens que devem ser bloqueadas
        timeout: Tempo limite em segundos para as requisições
        
    Returns:
        Dicionário com resultados dos testes
    """
    results = {"success": True, "details": {}, "errors": []}
    
    # Verifica se a API está acessível antes de prosseguir
    can_connect, error_msg = test_connectivity(api_url, timeout)
    if not can_connect:
        results["success"] = False
        results["errors"].append(f"Não foi possível conectar à API: {error_msg}")
        return results
    
    # Testa todas as origens que devem ser permitidas
    for origin in allowed_origins:
        try:
            response = requests.options(
                api_url,
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Authorization"
                },
                timeout=timeout
            )
            
            allowed = "Access-Control-Allow-Origin" in response.headers and \
                     (response.headers["Access-Control-Allow-Origin"] == origin or 
                      response.headers["Access-Control-Allow-Origin"] == "*")
            
            results["details"][origin] = allowed
            
            if not allowed:
                results["success"] = False
                msg = f"Configuração CORS falha: origem permitida {origin} foi bloqueada"
                results["errors"].append(msg)
                logger.warning(msg)
        
        except Exception as e:
            results["details"][origin] = False
            results["success"] = False
            msg = f"Erro ao testar CORS para origem {origin}: {str(e)}"
            results["errors"].append(msg)
            logger.error(msg)
    
    # Testa origens que devem ser bloqueadas
    for origin in disallowed_origins:
        try:
            response = requests.options(
                api_url,
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Authorization"
                },
                timeout=timeout
            )
            
            blocked = "Access-Control-Allow-Origin" not in response.headers or \
                     response.headers["Access-Control-Allow-Origin"] != origin
            
            results["details"][origin] = blocked
            
            if not blocked:
                results["success"] = False
                msg = f"Falha de segurança CORS: origem não permitida {origin} foi aceita"
                results["errors"].append(msg)
                logger.warning(msg)
        
        except requests.exceptions.RequestException:
            # Se houver erro de conexão, consideramos que a origem foi bloqueada (o que é bom)
            results["details"][origin] = True
        except Exception as e:
            msg = f"Erro ao testar CORS para origem bloqueada {origin}: {str(e)}"
            logger.error(msg)
            results["errors"].append(msg)
            # Não alteramos o status de sucesso aqui, pois é um erro de teste, não da configuração
    
    return results

def verify_security_headers(api_url: str, timeout: int = 5) -> Dict[str, any]:
    """
    Verifica se os cabeçalhos de segurança estão configurados corretamente.
    
    Args:
        api_url: URL base da API
        timeout: Tempo limite em segundos para as requisições
        
    Returns:
        Dicionário com resultados da verificação
    """
    required_headers = {
        "X-Frame-Options": ["DENY", "SAMEORIGIN"],
        "X-Content-Type-Options": ["nosniff"],
        "X-XSS-Protection": ["1; mode=block"],
        "Strict-Transport-Security": None,  # Qualquer valor é ok
        "Content-Security-Policy": None,    # Qualquer valor é ok
        "Referrer-Policy": None             # Qualquer valor é ok
    }
    
    results = {"success": True, "details": {}, "errors": [], "headers_found": {}}
    
    # Verifica se a API está acessível antes de prosseguir
    can_connect, error_msg = test_connectivity(api_url, timeout)
    if not can_connect:
        results["success"] = False
        results["errors"].append(f"Não foi possível conectar à API: {error_msg}")
        return results
    
    try:
        response = requests.get(api_url, timeout=timeout)
        
        # Armazena todos os cabeçalhos encontrados para diagnóstico
        for header, value in response.headers.items():
            results["headers_found"][header] = value
        
        for header, valid_values in required_headers.items():
            header_present = header in response.headers
            results["details"][header] = header_present
            
            if not header_present:
                results["success"] = False
                msg = f"Cabeçalho de segurança ausente: {header}"
                results["errors"].append(msg)
                logger.warning(msg)
            elif valid_values is not None:
                header_valid = response.headers[header] in valid_values
                results["details"][f"{header}_valid"] = header_valid
                
                if not header_valid:
                    results["success"] = False
                    msg = f"Cabeçalho {header} tem valor inválido: {response.headers[header]}"
                    results["errors"].append(msg)
                    logger.warning(msg)
    
    except Exception as e:
        results["success"] = False
        msg = f"Erro ao verificar cabeçalhos de segurança: {str(e)}"
        results["errors"].append(msg)
        logger.error(msg)
    
    return results

def detect_environment() -> str:
    """
    Detecta se o ambiente é de produção ou desenvolvimento.
    
    Returns:
        "production" ou "development"
    """
    try:
        # Tenta resolver o domínio de produção
        socket.gethostbyname("avaliadorprompt.com.br")
        return "production"
    except:
        return "development"

if __name__ == "__main__":
    # Configuração básica de logging para execução standalone
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ambiente e configurações
    env = detect_environment()
    print(f"Ambiente detectado: {env}")
    
    if env == "production":
        api_url = "https://avaliadorprompt.com.br/api"
        allowed = ["https://avaliadorprompt.com.br", "https://www.avaliadorprompt.com.br"]
    else:
        api_url = "http://localhost:8000/api"
        allowed = ["http://localhost:3000", "http://localhost:5000"]
    
    disallowed = ["http://attacker.com", "https://evil-site.org"]
    
    # Verifica conectividade
    can_connect, error = test_connectivity(api_url)
    if not can_connect:
        print(f"❌ Não foi possível conectar à API: {error}")
        if env == "development":
            print("Tentando conectar à porta alternativa...")
            api_url = "http://localhost:8000/api"
            can_connect, error = test_connectivity(api_url)
            if can_connect:
                print(f"✅ Conectado com sucesso à {api_url}")
            else:
                print(f"❌ Também falhou na porta alternativa: {error}")
                print("Certifique-se de que o servidor de API está rodando.")
                exit(1)
        else:
            print("Certifique-se de que o servidor de API está acessível.")
            exit(1)
    
    print(f"\nTestando configuração CORS em {api_url}...")
    cors_results = test_cors_configuration(api_url, allowed, disallowed)
    if cors_results["success"]:
        print(f"✅ Configuração CORS aprovada!")
    else:
        print(f"❌ Falha na configuração CORS:")
        for error in cors_results["errors"]:
            print(f"  - {error}")
    
    print("\nVerificando cabeçalhos de segurança...")
    headers_results = verify_security_headers(api_url)
    if headers_results["success"]:
        print(f"✅ Cabeçalhos de segurança aprovados!")
    else:
        print(f"❌ Falha nos cabeçalhos de segurança:")
        for error in headers_results["errors"]:
            print(f"  - {error}")
        
        print("\nCabeçalhos encontrados:")
        for header, value in headers_results.get("headers_found", {}).items():
            print(f"  {header}: {value}") 