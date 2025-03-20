#!/usr/bin/env python3
"""
Script para iniciar o servidor FastAPI com verificações de segurança.
Executa verificações de segurança após a inicialização do servidor para garantir
que todas as configurações de segurança estejam funcionando corretamente.
"""

import os
import sys
import time
import threading
import logging
import subprocess
import uvicorn
from typing import Optional

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("server_runner")

def run_security_check(api_url: str) -> bool:
    """
    Executa a verificação de segurança no servidor.
    
    Args:
        api_url: URL da API para verificar
        
    Returns:
        True se todas as verificações passaram, False caso contrário
    """
    # Caminho para o script de verificação de segurança
    script_path = os.path.join(os.path.dirname(__file__), "tools", "security_checker.py")
    
    # Executa o script com a URL especificada
    result = subprocess.run(
        [sys.executable, script_path, "--url", api_url, "--env", "dev"],
        capture_output=True,
        text=True
    )
    
    # Exibe a saída do script
    if result.stdout:
        for line in result.stdout.splitlines():
            logger.info(f"Security Check: {line}")
    
    if result.stderr:
        for line in result.stderr.splitlines():
            logger.error(f"Security Check Error: {line}")
    
    # Retorna True se o código de saída for 0 (sucesso)
    return result.returncode == 0

def wait_for_server(host: str, port: int, timeout: int = 30) -> bool:
    """
    Aguarda o servidor iniciar e estar disponível.
    
    Args:
        host: Endereço do servidor
        port: Porta do servidor
        timeout: Tempo máximo de espera em segundos
        
    Returns:
        True se o servidor estiver disponível, False caso contrário
    """
    import socket
    import time
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Tenta estabelecer uma conexão TCP com o servidor
            with socket.create_connection((host, port), timeout=1):
                # Se a conexão for bem-sucedida, o servidor está ativo
                time.sleep(2)  # Dê algum tempo para o servidor inicializar completamente
                return True
        except (socket.timeout, ConnectionRefusedError):
            # Se a conexão falhar, espere um pouco e tente novamente
            time.sleep(1)
    
    return False

def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = True) -> None:
    """
    Inicia o servidor Uvicorn com a aplicação FastAPI.
    
    Args:
        host: Endereço para servir a API
        port: Porta para servir a API
        reload: Se deve recarregar o servidor ao detectar alterações nos arquivos
    """
    logger.info(f"Iniciando servidor em {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

def check_security_worker(api_url: str) -> None:
    """
    Thread worker para executar verificações de segurança após o servidor iniciar.
    
    Args:
        api_url: URL da API para verificar
    """
    logger.info("Iniciando verificações de segurança...")
    
    # Aguarda o servidor iniciar
    if not wait_for_server("127.0.0.1", 8000):
        logger.error("Timeout ao esperar o servidor iniciar. Pulando verificações de segurança.")
        return
    
    logger.info("Servidor iniciado. Executando verificações de segurança...")
    
    # Executa a verificação de segurança
    if run_security_check(api_url):
        logger.info("✅ Todas as verificações de segurança passaram com sucesso!")
    else:
        logger.warning("❌ Algumas verificações de segurança falharam!")
        logger.warning("⚠️ Por favor, revise as configurações de segurança da aplicação.")
        
    logger.info("Para verificações detalhadas, execute: python -m tools.security_checker")

def main() -> None:
    """Função principal para iniciar o servidor e executar verificações de segurança"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Iniciar servidor FastAPI com verificações de segurança")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Endereço para servir a API")
    parser.add_argument("--port", type=int, default=8000, help="Porta para servir a API")
    parser.add_argument("--no-reload", action="store_true", help="Desativar reload automático")
    parser.add_argument("--skip-security", action="store_true", help="Pular verificações de segurança")
    
    args = parser.parse_args()
    
    api_url = f"http://{args.host}:{args.port}/api"
    
    # Inicia a thread de verificação de segurança
    if not args.skip_security:
        security_thread = threading.Thread(
            target=check_security_worker,
            args=(api_url,),
            daemon=True
        )
        security_thread.start()
    
    # Inicia o servidor
    run_server(args.host, args.port, not args.no_reload)

if __name__ == "__main__":
    main() 