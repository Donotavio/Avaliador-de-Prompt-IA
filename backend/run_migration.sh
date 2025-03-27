#!/bin/bash
# Script para executar migrações usando o Alembic

# Diretório atual do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Definir ambiente padrão como desenvolvimento
ENVIRONMENT="development"
ENV_FILE=".env"

# Verificar parâmetros de linha de comando
if [ "$1" == "prod" ] || [ "$1" == "production" ]; then
    ENVIRONMENT="production"
    ENV_FILE=".env.production"
    echo "Modo: PRODUÇÃO"
else
    echo "Modo: DESENVOLVIMENTO (use './run_migration.sh prod' para ambiente de produção)"
fi

export ENVIRONMENT=$ENVIRONMENT

echo "Executando Alembic no ambiente de $ENVIRONMENT..."
echo "Diretório atual: $(pwd)"
echo "Arquivo $ENV_FILE existe: $([ -f $ENV_FILE ] && echo 'Sim' || echo 'Não')"

# Verificar se o arquivo de ambiente existe
if [ ! -f "$ENV_FILE" ]; then
    echo "ERRO: Arquivo $ENV_FILE não encontrado!"
    exit 1
fi

# Carregar variáveis do arquivo de ambiente
echo "Carregando configurações de $ENV_FILE"
export $(grep -v '^#' $ENV_FILE | xargs)

# Mostrar as variáveis do banco de dados (sem a senha)
echo "Informações de conexão com o banco de dados:"
echo "DATABASE_URL=$DATABASE_URL"
echo "USER_DATABASE=$USER_DATABASE"
echo "DATABASE=$DATABASE"
echo "DATABASE_PASSWORD=[oculto]"

# Verificar se as variáveis essenciais estão definidas
if [ -z "$DATABASE_URL" ] || [ -z "$USER_DATABASE" ] || [ -z "$DATABASE" ] || [ -z "$DATABASE_PASSWORD" ]; then
    echo "ERRO: Variáveis de conexão com banco de dados não definidas corretamente no arquivo $ENV_FILE"
    exit 1
fi

# Executar o Alembic para upgrade
echo "Iniciando migração..."
alembic upgrade head

# Verificar resultado
if [ $? -eq 0 ]; then
    echo "✅ Migração concluída com sucesso!"
else
    echo "❌ Erro ao executar migração!"
    exit 1
fi 