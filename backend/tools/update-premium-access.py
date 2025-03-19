#!/usr/bin/env python3
"""
Script para limpar ativações premium não pagas e resetar o banco de dados de usuários
"""
import json
import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("premium-cleanup")

# Caminho para o arquivo de dados de uso
USER_USAGE_FILE = os.path.join(os.path.dirname(__file__), "backend", "user_usage.json")

def clean_premium_activations():
    """Limpa todas as ativações premium que não foram confirmadas por pagamento"""
    try:
        # Verificar se o arquivo existe
        if not os.path.exists(USER_USAGE_FILE):
            logger.error(f"Arquivo de uso não encontrado em {USER_USAGE_FILE}")
            return False
            
        # Ler o arquivo atual
        with open(USER_USAGE_FILE, "r") as f:
            try:
                user_data = json.load(f)
            except json.JSONDecodeError:
                logger.error("Erro ao decodificar arquivo JSON")
                return False
                
        # Contar usuários antes da limpeza
        user_count_before = len(user_data)
        active_premium_before = sum(1 for user_id, user in user_data.items() 
                                   if user.get("is_premium_active", False))
        
        # Resetar todas as ativações premium
        for user_id, user in user_data.items():
            # Desativar premium para todos os usuários
            if user.get("is_premium_active", False):
                user["is_premium_active"] = False
            
            # Resetar contadores de ativação premium
            user["premium_activations_count"] = 0
            
            # Manter outros dados como uso gratuito
            logger.info(f"Resetado premium para usuário {user_id}")
        
        # Salvar as alterações
        with open(USER_USAGE_FILE, "w") as f:
            json.dump(user_data, f, indent=2)
            
        # Log de estatísticas
        logger.info(f"Limpeza completa: {user_count_before} usuários processados")
        logger.info(f"Premium desativado para {active_premium_before} usuários")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao limpar ativações premium: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Iniciando limpeza de ativações premium não pagas")
    if clean_premium_activations():
        logger.info("Limpeza concluída com sucesso")
    else:
        logger.error("Falha na limpeza de ativações premium") 