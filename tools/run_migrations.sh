#!/bin/bash
# Script para executar migrações do banco de dados manualmente
# Use este script quando precisar atualizar o esquema do banco sem fazer um deploy completo

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

echo -e "${YELLOW}Este script executará as migrações do banco de dados usando Alembic.${NC}"
echo -e "${YELLOW}Ensure you have SSH access to the server before continuing.${NC}"
echo -e "${YELLOW}Pressione ENTER para continuar ou CTRL+C para cancelar...${NC}"
read

# Executando migrações
echo -e "${YELLOW}Conectando ao servidor e executando migrações...${NC}"

ssh $VPS_USER@$VPS_IP << EOF
  echo "Conectado ao servidor. Executando migrações..."
  cd $APP_DIR/backend
  source ../venv/bin/activate
  
  # Verifica a conexão com o banco de dados
  echo "Verificando conexão com o banco de dados..."
  python -c 'from services.database import test_db_connection; print("Conexão com banco de dados:", "OK" if test_db_connection() else "FALHA")'
  
  # Executa as migrações
  echo "Executando migrações Alembic..."
  alembic upgrade head
  
  echo "Migrações concluídas."
EOF

echo -e "${GREEN}Processo de migração concluído!${NC}"
echo -e "${YELLOW}Verificando status das migrações...${NC}"

ssh $VPS_USER@$VPS_IP << EOF
  cd $APP_DIR/backend
  source ../venv/bin/activate
  echo "Versão atual do banco de dados:"
  alembic current
EOF

echo -e "${GREEN}Processo completo.${NC}"
