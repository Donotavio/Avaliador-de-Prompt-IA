#!/bin/bash
# Script para executar migrações usando o Alembic no ambiente de produção

# Diretório atual do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Definir ambiente como produção
export ENVIRONMENT=production

echo "Executando Alembic no ambiente de produção..."
echo "Diretório atual: $(pwd)"
echo "Arquivo .env.production existe: $([ -f .env.production ] && echo 'Sim' || echo 'Não')"

# Mostrar as variáveis do banco de dados (sem a senha)
if [ -f .env.production ]; then
  echo "Conteúdo das variáveis DATABASE (sem senhas):"
  grep -i "DATABASE\|USER_DATABASE" .env.production | grep -v "PASSWORD"
fi

# Definir explicitamente as variáveis do banco de dados
export DATABASE_URL="srv1783.hstgr.io" 
export USER_DATABASE="u414788967_don"
export DATABASE="u414788967_prompt_prod"
export DATABASE_PASSWORD="o75Qr?OC^"

# Mostrar variáveis configuradas
echo "Variáveis configuradas:"
echo "DATABASE_URL=$DATABASE_URL"
echo "USER_DATABASE=$USER_DATABASE"
echo "DATABASE=$DATABASE"
echo "DATABASE_PASSWORD=[oculto]"

# Executar o Alembic para upgrade
alembic upgrade head

echo "Migração concluída!" 