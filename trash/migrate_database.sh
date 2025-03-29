#!/bin/bash
# Script para migrar o banco de dados usando Alembic
# Este script deve ser executado na VPS após o deploy da aplicação

set -e  # Encerra o script se qualquer comando falhar

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configurações
VPS_IP="69.62.101.14"
VPS_USER="appuser"
APP_DIR="/var/www/avaliadorprompt"

# Função para executar comando remoto
execute_remote() {
    ssh $1@$VPS_IP "$2"
}

# Verifica status do banco de dados
echo -e "${YELLOW}Verificando conexão com o banco de dados...${NC}"
execute_remote $VPS_USER "cd $APP_DIR/backend && source $APP_DIR/venv/bin/activate && python -c 'from services.database import test_db_connection; print(\"Conexão com banco de dados: \", \"OK\" if test_db_connection() else \"FALHA\")'"

# Executa as migrações Alembic
echo -e "${YELLOW}Executando as migrações do banco de dados...${NC}"
execute_remote $VPS_USER "cd $APP_DIR/backend && source $APP_DIR/venv/bin/activate && alembic upgrade head"

echo -e "${GREEN}Migrações do banco de dados concluídas com sucesso!${NC}"
