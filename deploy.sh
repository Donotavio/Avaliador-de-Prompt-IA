#!/bin/bash
# Script de deploy para o Avaliador de Prompt IA
# Execute este script a partir do diretório raiz do projeto local

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

echo -e "${GREEN}Iniciando deploy do Avaliador de Prompt IA para VPS ($VPS_IP)...${NC}"

# Compila o frontend
echo -e "${YELLOW}Compilando o frontend...${NC}"
cd frontend
npm install
npm run build
cd ..

# Prepara o arquivo .env.production para o backend
echo -e "${YELLOW}Preparando arquivo .env.production...${NC}"

# Se o arquivo .env.production não existir, cria a partir do .env
if [ ! -f backend/.env.production ]; then
    cp backend/.env backend/.env.production
    echo -e "${YELLOW}Arquivo .env.production criado. Você deve revisar e atualizar os valores para produção.${NC}"
    echo -e "${YELLOW}Pressione qualquer tecla para continuar ou Ctrl+C para cancelar e editar o arquivo.${NC}"
    read -n 1 -s
fi

# Verifica se o diretório da aplicação existe no servidor
echo -e "${YELLOW}Verificando e criando diretório da aplicação no servidor...${NC}"
ssh $VPS_USER@$VPS_IP "mkdir -p $APP_DIR/backend $APP_DIR/frontend"

# Envia arquivos do frontend para VPS
echo -e "${YELLOW}Enviando arquivos do frontend...${NC}"
rsync -avz --progress frontend/build/ $VPS_USER@$VPS_IP:$APP_DIR/frontend/build/

# Envia arquivos do backend para VPS
echo -e "${YELLOW}Enviando arquivos do backend...${NC}"
rsync -avz --progress --exclude '__pycache__' --exclude '*.pyc' backend/ $VPS_USER@$VPS_IP:$APP_DIR/backend/

# Configura ambiente Python no servidor
echo -e "${YELLOW}Configurando ambiente Python no servidor...${NC}"
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
cd /var/www/avaliadorprompt
python3 -m venv venv
source venv/bin/activate
cd backend
pip install -r requirements.txt
pip install gunicorn
ENDSSH

# Reinicia o serviço backend
echo -e "${YELLOW}Reiniciando serviço backend...${NC}"
ssh root@$VPS_IP "systemctl restart avaliador-api"

# Reinicia o Nginx
echo -e "${YELLOW}Reiniciando Nginx...${NC}"
ssh root@$VPS_IP "systemctl restart nginx"

echo -e "${GREEN}Deploy concluído com sucesso!${NC}"
echo -e "${YELLOW}Acesse o site em: https://avaliadorprompt.com.br${NC}"
echo -e "${YELLOW}Verifique os logs do backend com: ssh root@$VPS_IP 'journalctl -u avaliador-api -f'${NC}"
