#!/bin/bash
# Script de provisionamento para VPS do Avaliador de Prompt IA
# Executa como root na VPS para configurar o ambiente

set -e  # Encerra o script se qualquer comando falhar

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Iniciando provisionamento da VPS para Avaliador de Prompt IA...${NC}"

# Atualiza o sistema
echo -e "${YELLOW}Atualizando pacotes do sistema...${NC}"
apt-get update
apt-get upgrade -y

# Instala dependências necessárias
echo -e "${YELLOW}Instalando dependências...${NC}"
apt-get install -y python3 python3-pip python3-venv nginx ufw git certbot python3-certbot-nginx fail2ban

# Configura firewall
echo -e "${YELLOW}Configurando firewall...${NC}"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# Configura fail2ban para proteção contra força bruta
echo -e "${YELLOW}Configurando fail2ban...${NC}"
systemctl enable fail2ban
systemctl start fail2ban

# Cria usuário para aplicação
echo -e "${YELLOW}Criando usuário para aplicação...${NC}"
adduser --disabled-password --gecos "" appuser
mkdir -p /home/appuser/.ssh
cp /root/.ssh/authorized_keys /home/appuser/.ssh/
chown -R appuser:appuser /home/appuser/.ssh
chmod 700 /home/appuser/.ssh
chmod 600 /home/appuser/.ssh/authorized_keys

# Configurações do diretório da aplicação
echo -e "${YELLOW}Configurando diretório da aplicação...${NC}"
mkdir -p /var/www/avaliadorprompt
chown -R appuser:appuser /var/www/avaliadorprompt

# Configuração do Nginx
echo -e "${YELLOW}Configurando Nginx...${NC}"
cat > /etc/nginx/sites-available/avaliadorprompt.conf << 'EOL'
server {
    listen 80;
    server_name avaliadorprompt.com.br www.avaliadorprompt.com.br;
    server_tokens off;
    
    # Redirect all HTTP requests to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name avaliadorprompt.com.br www.avaliadorprompt.com.br;
    server_tokens off;
    
    # Buffer size limits to prevent buffer overflow attacks
    client_body_buffer_size 10K;
    client_header_buffer_size 1k;
    client_max_body_size 10m;
    large_client_header_buffers 2 1k;
    
    # Timeouts to prevent slow HTTP attacks
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;
    
    # SSL will be configured by certbot

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
    limit_conn conn_limit_per_ip 20;
    
    # Frontend static files
    root /var/www/avaliadorprompt/frontend/build;
    index index.html;
    
    # Frontend route handling
    location / {
        try_files $uri $uri/ /index.html;
        expires 1d;
    }
    
    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    # API requests
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://unix:/tmp/avaliador-api.sock;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 120s;
    }
    
    # Additional rate limits for sensitive endpoints
    location /api/auth/login {
        limit_req zone=api_limit burst=5 nodelay;
        proxy_pass http://unix:/tmp/avaliador-api.sock;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 60s;
    }
    
    # Deny access to dot files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOL

ln -sf /etc/nginx/sites-available/avaliadorprompt.conf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Configura systemd para o backend
echo -e "${YELLOW}Configurando serviço systemd para backend...${NC}"
cat > /etc/systemd/system/avaliador-api.service << 'EOL'
[Unit]
Description=Avaliador Prompt API Service
After=network.target

[Service]
User=appuser
Group=appuser
WorkingDirectory=/var/www/avaliadorprompt/backend
ExecStart=/var/www/avaliadorprompt/venv/bin/gunicorn -c gunicorn_conf.py main:app
Restart=always
RestartSec=5
Environment="PATH=/var/www/avaliadorprompt/venv/bin"
EnvironmentFile=/var/www/avaliadorprompt/backend/.env.production

[Install]
WantedBy=multi-user.target
EOL

# Cria diretório para logs
mkdir -p /var/log/gunicorn
chown -R appuser:appuser /var/log/gunicorn

# Reinicia serviços
echo -e "${YELLOW}Reiniciando serviços...${NC}"
systemctl restart nginx
systemctl daemon-reload

echo -e "${GREEN}Provisionamento concluído!${NC}"
echo -e "${YELLOW}Próximos passos:${NC}"
echo -e "1. Faça deploy do código com o script deploy.sh"
echo -e "2. Configure o SSL com o comando: certbot --nginx -d avaliadorprompt.com.br -d www.avaliadorprompt.com.br"
echo -e "3. Inicie o serviço backend: systemctl start avaliador-api"
