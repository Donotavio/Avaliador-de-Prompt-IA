#!/usr/bin/env python3
"""
Script para iniciar o servidor FastAPI de forma simplificada em produção.
"""

import os
import sys
import logging
import traceback
import uvicorn

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("server_runner")

def main() -> int:
    """Função principal para iniciar o servidor de forma simplificada"""
    try:
        logger.info("Iniciando servidor...")
        
        # Verificar se o arquivo .env.production existe
        if os.path.exists(".env.production"):
            logger.info("Arquivo .env.production encontrado")
        else:
            logger.error("Arquivo .env.production não encontrado!")
            
        # Iniciar servidor diretamente (evita importar main.py antecipadamente)
        logger.info("Iniciando servidor uvicorn...")
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            log_level="debug"
        )
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")
        traceback.print_exc()
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 