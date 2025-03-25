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
FRONTEND_DIR="$APP_DIR/frontend"
BACKEND_DIR="$APP_DIR/backend"

echo -e "${GREEN}Iniciando deploy do Avaliador de Prompt IA para VPS ($VPS_IP)...${NC}"

# Prepara o arquivo .env.production para o backend
echo -e "${YELLOW}Preparando arquivo .env.production...${NC}"

# Se o arquivo .env.production não existir, cria a partir do .env
if [ ! -f backend/.env.production ]; then
    cp backend/.env backend/.env.production
    echo -e "${YELLOW}Arquivo .env.production criado. Você deve revisar e atualizar os valores para produção.${NC}"
    echo -e "${YELLOW}Pressione qualquer tecla para continuar ou Ctrl+C para cancelar e editar o arquivo.${NC}"
    read -n 1 -s
fi

# Atualizar CORS_ORIGINS no .env.production
if grep -q "CORS_ORIGINS" backend/.env.production; then
    sed -i '' 's/CORS_ORIGINS=.*/CORS_ORIGINS=https:\/\/avaliadorprompt.com,http:\/\/avaliadorprompt.com,https:\/\/www.avaliadorprompt.com,http:\/\/www.avaliadorprompt.com/' backend/.env.production
else
    echo "CORS_ORIGINS=https://avaliadorprompt.com,http://avaliadorprompt.com,https://www.avaliadorprompt.com,http://www.avaliadorprompt.com" >> backend/.env.production
fi

# Prepara o frontend para produção
echo -e "${YELLOW}Compilando o frontend para produção...${NC}"
cd frontend
npm install
npm run build
cd ..

# Verifica se os diretórios da aplicação existem no servidor
echo -e "${YELLOW}Verificando e criando diretórios da aplicação no servidor...${NC}"
ssh $VPS_USER@$VPS_IP "mkdir -p $BACKEND_DIR"
ssh $VPS_USER@$VPS_IP "mkdir -p $FRONTEND_DIR"

# Envia arquivos do backend para VPS
echo -e "${YELLOW}Enviando arquivos do backend...${NC}"
rsync -avz --progress --exclude '__pycache__' --exclude '*.pyc' backend/ $VPS_USER@$VPS_IP:$BACKEND_DIR/

# Garante que o arquivo .env.production tenha as permissões corretas
echo -e "${YELLOW}Configurando permissões do arquivo .env.production...${NC}"
ssh $VPS_USER@$VPS_IP "chmod 600 $BACKEND_DIR/.env.production"

# Envia arquivos do frontend para VPS
echo -e "${YELLOW}Enviando arquivos do frontend...${NC}"
rsync -avz --progress frontend/build/ $VPS_USER@$VPS_IP:$FRONTEND_DIR/

# Cria o diretório de logs necessário para o gunicorn
echo -e "${YELLOW}Criando diretório de logs...${NC}"
ssh root@$VPS_IP "mkdir -p /var/log/avaliador-api && chown -R $VPS_USER:$VPS_USER /var/log/avaliador-api"

# Cria configuração do Nginx
echo -e "${YELLOW}Criando configuração do Nginx...${NC}"
cat > avaliadorprompt.conf << EOF
server {
    listen 80;
    server_name avaliadorprompt.com www.avaliadorprompt.com;

    # Frontend
    location / {
        root $FRONTEND_DIR;
        try_files \$uri \$uri/ /index.html;
        index index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 90s;
    }

    # Log de erros e acessos
    access_log /var/log/nginx/avaliadorprompt.access.log;
    error_log /var/log/nginx/avaliadorprompt.error.log;
}
EOF

# Envia o arquivo de configuração Nginx
echo -e "${YELLOW}Enviando configuração do Nginx...${NC}"
scp avaliadorprompt.conf root@$VPS_IP:/etc/nginx/sites-available/
ssh root@$VPS_IP "ln -sf /etc/nginx/sites-available/avaliadorprompt.conf /etc/nginx/sites-enabled/ && rm -f /etc/nginx/sites-enabled/default"

# Instala o pacote local em vez de usar o repositório GitHub
echo -e "${YELLOW}Configurando ambiente Python no servidor...${NC}"
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
cd /var/www/avaliadorprompt
python3 -m venv venv
source venv/bin/activate
cd backend
pip install -r requirements.txt
pip install gunicorn
pip install pymysql cryptography bleach tinycss2 email-validator
# Instalar o pacote localmente
pip install -e .

# Testar conexão com o banco de dados
echo "Testando conexão com o banco de dados..."
python -c "
import pymysql
import os
from dotenv import load_dotenv
load_dotenv('.env.production')
try:
    db_url = os.getenv('DATABASE_URL')
    print(f'Testando conexão com: {db_url}')
    conn = pymysql.connect(
        host='srv1783.hstgr.io',
        user='u414788967_don',
        password=os.getenv('DATABASE_PASSWORD'),
        database='u414788967_prom_evaluate',
        port=3306
    )
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    result = cursor.fetchone()
    print(f'Conexão com banco de dados bem-sucedida! Resultado: {result}')
    conn.close()
except Exception as e:
    print(f'Erro ao conectar ao banco de dados: {e}')
"
ENDSSH

# Execute as migrações de banco de dados
echo -e "${YELLOW}Executando migrações do banco de dados com Alembic...${NC}"
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
cd /var/www/avaliadorprompt/backend
source ../venv/bin/activate
# Instala o alembic se não estiver instalado
pip install alembic
# Executa as migrações
alembic upgrade head
ENDSSH

# Envia o arquivo de serviço systemd
echo -e "${YELLOW}Configurando serviço systemd...${NC}"
scp backend/avaliador-api.service root@$VPS_IP:/etc/systemd/system/
ssh root@$VPS_IP "systemctl daemon-reload"

# Reinicia o serviço backend
echo -e "${YELLOW}Reiniciando serviço backend...${NC}"
ssh root@$VPS_IP "systemctl restart avaliador-api"
ssh root@$VPS_IP "systemctl status avaliador-api"

# Verifica se a API está respondendo
echo -e "${YELLOW}Verificando se a API está respondendo...${NC}"
ssh root@$VPS_IP "sleep 5 && curl -s http://localhost:8000/api/health || echo 'API não está respondendo localmente'"

# Reinicia o Nginx
echo -e "${YELLOW}Reiniciando Nginx...${NC}"
ssh root@$VPS_IP "nginx -t && systemctl restart nginx"

echo -e "${GREEN}Deploy completo concluído com sucesso!${NC}"
echo -e "${YELLOW}Frontend e backend estão implantados em: http://avaliadorprompt.com${NC}"

echo -e "${YELLOW}Dicas para depuração:${NC}"
echo -e "1. Verificar logs do serviço backend: ${GREEN}ssh root@$VPS_IP 'journalctl -u avaliador-api -f'${NC}"
echo -e "2. Verificar logs do Nginx: ${GREEN}ssh root@$VPS_IP 'tail -f /var/log/nginx/avaliadorprompt.error.log'${NC}"
echo -e "3. Verificar status do serviço: ${GREEN}ssh root@$VPS_IP 'systemctl status avaliador-api'${NC}"
echo -e "4. Testar API diretamente: ${GREEN}ssh root@$VPS_IP 'curl -v http://localhost:8000/api/health'${NC}"

# Configuração de SSL
echo -e "${YELLOW}Deseja configurar o SSL para o site agora? (y/n)${NC}"
read -r configure_ssl

if [[ "$configure_ssl" =~ ^[Yy]$ ]]; then
  echo -e "${YELLOW}Configurando SSL com Certbot...${NC}"
  ssh root@$VPS_IP "apt-get update && apt-get install -y certbot python3-certbot-nginx && certbot --nginx -d avaliadorprompt.com -d www.avaliadorprompt.com"
  
  echo -e "${GREEN}SSL configurado com sucesso!${NC}"
  echo -e "${YELLOW}Acesse o site em: https://avaliadorprompt.com${NC}"
else
  echo -e "${YELLOW}Você pode configurar o SSL mais tarde executando:${NC}"
  echo -e "${YELLOW}ssh root@$VPS_IP \"apt-get update && apt-get install -y certbot python3-certbot-nginx && certbot --nginx -d avaliadorprompt.com -d www.avaliadorprompt.com\"${NC}"
fi
