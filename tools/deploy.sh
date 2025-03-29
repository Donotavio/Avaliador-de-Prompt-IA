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

# Definindo variáveis para o banco de dados
DB_HOST="srv1783.hstgr.io"
DB_PORT="3306"
DB_USER="u414788967_don"
DB_NAME="u414788967_prompt_prod"
DB_PASSWORD="o75Qr?OC^"

# Configuração de email
EMAIL_HOST="smtp.hostinger.com"
EMAIL_PORT="465"
EMAIL_USER="contato@avaliadorprompt.com"
EMAIL_PASSWORD="d=q!M@p=L3"
EMAIL_FROM="contato@avaliadorprompt.com"

# Usando a senha diretamente sem codificação manual
# A conexão SQLAlchemy tratará isso automaticamente
DATABASE_URL="mysql+pymysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo -e "${YELLOW}Atualizando credenciais do banco de dados no .env.production...${NC}"

# Atualiza DATABASE_URL com a string de conexão completa (usando aspas simples)
if grep -q "DATABASE_URL" backend/.env.production; then
    sed -i '' "s|DATABASE_URL=.*|DATABASE_URL='$DATABASE_URL'|" backend/.env.production
else
    echo "DATABASE_URL='$DATABASE_URL'" >> backend/.env.production
fi

# Mantém também as variáveis individuais (para compatibilidade)
if grep -q "USER_DATABASE" backend/.env.production; then
    sed -i '' "s/USER_DATABASE=.*/USER_DATABASE=\"$DB_USER\"/" backend/.env.production
else
    echo "USER_DATABASE=\"$DB_USER\"" >> backend/.env.production
fi

if grep -q "DATABASE=" backend/.env.production; then
    sed -i '' "s/DATABASE=.*/DATABASE=\"$DB_NAME\"/" backend/.env.production
else
    echo "DATABASE=\"$DB_NAME\"" >> backend/.env.production
fi

if grep -q "DATABASE_PASSWORD" backend/.env.production; then
    sed -i '' "s/DATABASE_PASSWORD=.*/DATABASE_PASSWORD=\"$DB_PASSWORD\"/" backend/.env.production
else
    echo "DATABASE_PASSWORD=\"$DB_PASSWORD\"" >> backend/.env.production
fi

# Atualiza as credenciais de email no .env.production
echo -e "${YELLOW}Atualizando credenciais de email no .env.production...${NC}"

# Atualiza EMAIL_HOST
if grep -q "EMAIL_HOST" backend/.env.production; then
    sed -i '' "s/EMAIL_HOST=.*/EMAIL_HOST=\"$EMAIL_HOST\"/" backend/.env.production
else
    echo "EMAIL_HOST=\"$EMAIL_HOST\"" >> backend/.env.production
fi

# Atualiza EMAIL_PORT
if grep -q "EMAIL_PORT" backend/.env.production; then
    sed -i '' "s/EMAIL_PORT=.*/EMAIL_PORT=$EMAIL_PORT/" backend/.env.production
else
    echo "EMAIL_PORT=$EMAIL_PORT" >> backend/.env.production
fi

# Atualiza EMAIL_USER
if grep -q "EMAIL_USER" backend/.env.production; then
    sed -i '' "s/EMAIL_USER=.*/EMAIL_USER=\"$EMAIL_USER\"/" backend/.env.production
else
    echo "EMAIL_USER=\"$EMAIL_USER\"" >> backend/.env.production
fi

# Atualiza EMAIL_PASSWORD com a senha correta
if grep -q "EMAIL_PASSWORD" backend/.env.production; then
    sed -i '' "s/EMAIL_PASSWORD=.*/EMAIL_PASSWORD=\"$EMAIL_PASSWORD\"/" backend/.env.production
else
    echo "EMAIL_PASSWORD=\"$EMAIL_PASSWORD\"" >> backend/.env.production
fi

# Atualiza EMAIL_FROM
if grep -q "EMAIL_FROM" backend/.env.production; then
    sed -i '' "s/EMAIL_FROM=.*/EMAIL_FROM=\"$EMAIL_FROM\"/" backend/.env.production
else
    echo "EMAIL_FROM=\"$EMAIL_FROM\"" >> backend/.env.production
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
import urllib.parse

load_dotenv('.env.production')

# Obtém DATABASE_URL primeiro
db_url = os.getenv('DATABASE_URL', '')
print(f'DATABASE_URL encontrado: {db_url}')

try:
    # Verifica se é uma URL válida com usuário:senha@host:porta/database
    if 'mysql+pymysql://' in db_url:
        print('Tentando conexão direta com DATABASE_URL')
        
        # Remove o prefixo e divide por @
        url_parts = db_url.replace('mysql+pymysql://', '').split('@')
        if len(url_parts) != 2:
            raise ValueError('Formato de URL inválido')
            
        user_pass = url_parts[0].split(':')
        if len(user_pass) != 2:
            raise ValueError('Formato de usuário/senha inválido')
            
        host_port_db = url_parts[1].split('/')
        if len(host_port_db) != 2:
            raise ValueError('Formato de host/database inválido')
            
        host_port = host_port_db[0].split(':')
        
        # Extrair partes da URL
        db_user = user_pass[0]
        db_password = user_pass[1]
        db_host = host_port[0]
        db_port = int(host_port[1]) if len(host_port) > 1 else 3306
        db_name = host_port_db[1]
        
        print(f'Tentando conectar com: host={db_host}, port={db_port}, user={db_user}, db={db_name}')
        
        # Tenta conexão direta com os parâmetros extraídos
        conn = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        print(f'Conexão com banco de dados bem-sucedida usando DATABASE_URL! Resultado: {result}')
        conn.close()
    else:
        # Fallback para as variáveis separadas
        print('DATABASE_URL não encontrada ou inválida, usando variáveis individuais')
        db_host = os.getenv('DATABASE_URL', 'srv1783.hstgr.io')
        db_user = os.getenv('USER_DATABASE', 'u414788967_don')
        db_password = os.getenv('DATABASE_PASSWORD', '')
        db_name = os.getenv('DATABASE', 'u414788967_prompt_prod')
        
        print(f'Tentando conectar com: host={db_host}, user={db_user}, db={db_name}')
        
        conn = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=3306
        )
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        print(f'Conexão com banco de dados bem-sucedida usando variáveis separadas! Resultado: {result}')
        conn.close()
except Exception as e:
    print(f'Erro ao conectar ao banco de dados: {e}')
    
    # Tenta abordagem alternativa se a primeira falhar
    try:
        print('Tentando abordagem alternativa de conexão')
        # Obtém variáveis individuais
        db_host = os.getenv('DATABASE_URL', 'srv1783.hstgr.io')
        db_user = os.getenv('USER_DATABASE', 'u414788967_don')
        db_password = os.getenv('DATABASE_PASSWORD', '')
        db_name = os.getenv('DATABASE', 'u414788967_prompt_prod')
        
        print(f'Tentando conectar com: host={db_host}, user={db_user}, db={db_name}')
        
        conn = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=3306
        )
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        print(f'Conexão alternativa bem-sucedida! Resultado: {result}')
        conn.close()
    except Exception as e2:
        print(f'Erro na tentativa alternativa: {e2}')
"
ENDSSH

# Execute as migrações de banco de dados
echo -e "${YELLOW}Executando migrações do banco de dados com Alembic...${NC}"
ssh $VPS_USER@$VPS_IP << EOF
cd /var/www/avaliadorprompt/backend
source ../venv/bin/activate

# Instala o alembic se não estiver instalado
pip install alembic

# Define explicitamente as variáveis de ambiente para o banco de dados
export ENVIRONMENT=production

# Use variáveis separadas para evitar problemas de aspas e codificação
export DB_HOST="$DB_HOST"
export DB_PORT="$DB_PORT"
export DB_USER="$DB_USER"
export DB_PASSWORD="$DB_PASSWORD"
export DB_NAME="$DB_NAME"

# Executa as migrações usando variáveis separadas
echo "Executando migrações do banco de dados..."
python -c "
import os
import alembic.config

# Configura URL de conexão para alembic dinamicamente
os.environ['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}'

# Executa as migrações
alembic_args = ['--raiseerr', 'upgrade', 'head']
alembic.config.main(argv=alembic_args)
"

if [ \$? -eq 0 ]; then
    echo "Migrações executadas com sucesso!"
else
    echo "Falha ao executar migrações. Tentando abordagem alternativa..."
    # Tenta executar migrações diretamente
    cd /var/www/avaliadorprompt/backend
    PYTHONPATH=/var/www/avaliadorprompt/backend alembic upgrade head
fi
EOF

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
