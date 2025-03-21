# Deployment Guide for Avaliador de Prompt IA

Este guia descreve como fazer o deploy da aplicação Avaliador de Prompt IA na Hostinger.

## 1. Pré-requisitos

- Acesso SSH à sua conta Hostinger
- Domínio configurado (avaliadorprompt.com.br)
- Certificado SSL já instalado
- Git instalado no servidor

## 2. Preparação Inicial no Servidor

1. Conecte-se via SSH ao seu servidor Hostinger:

```bash
ssh usuariohostinger@seu-servidor-hostinger
```

2. Crie a estrutura de diretórios:

```bash
mkdir -p ~/avaliadorprompt.com.br/{backend,frontend}
mkdir -p /var/log/gunicorn
```

## 3. Deploy do Backend

1. Clone o repositório para o servidor:

```bash
cd ~/avaliadorprompt.com.br
git clone https://seu-repositorio-git.com/avaliador-prompt.git .
```

2. Configure um ambiente virtual Python:

```bash
cd ~/avaliadorprompt.com.br
python3 -m venv venv
source venv/bin/activate
cd backend
pip install -r requirements.txt
pip install gunicorn
```

3. Configure as variáveis de ambiente:

```bash
# Edite o arquivo .env.production com seus valores reais
nano .env.production
```

4. Configure o banco de dados:

```bash
# Se estiver usando SQLite
# ou execute as migrações para PostgreSQL se estiver usando
cd ~/avaliadorprompt.com.br/backend
python -m alembic upgrade head
```

5. Configure o serviço systemd:

```bash
# Edite o arquivo de serviço para refletir seu usuário e caminhos
nano ~/avaliadorprompt.com.br/backend/avaliador-api.service

# Copie para a pasta systemd
sudo cp ~/avaliadorprompt.com.br/backend/avaliador-api.service /etc/systemd/system/

# Inicie o serviço
sudo systemctl daemon-reload
sudo systemctl enable avaliador-api
sudo systemctl start avaliador-api
```

## 4. Deploy do Frontend

1. Instale o Node.js (se ainda não estiver instalado):

```bash
curl -sL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs
```

2. Compile o frontend:

```bash
cd ~/avaliadorprompt.com.br/frontend
npm install
npm run build
```

## 5. Configuração do Nginx

1. Configure o Nginx:

```bash
# Edite a configuração do Nginx para refletir seus caminhos
nano ~/avaliadorprompt.com.br/nginx-avaliador.conf

# Copie para a pasta de configuração do Nginx
sudo cp ~/avaliadorprompt.com.br/nginx-avaliador.conf /etc/nginx/sites-available/avaliadorprompt.com.br

# Ative o site
sudo ln -s /etc/nginx/sites-available/avaliadorprompt.com.br /etc/nginx/sites-enabled/

# Teste a configuração
sudo nginx -t

# Reinicie o Nginx
sudo systemctl restart nginx
```

## 6. Verificações Finais

1. Teste a aplicação acessando https://avaliadorprompt.com.br

2. Verifique os logs em caso de problemas:

```bash
# Logs do backend
sudo journalctl -u avaliador-api -f

# Logs do Nginx
sudo tail -f /var/log/nginx/error.log
```

## 7. Atualizações Futuras

Para atualizar a aplicação no futuro:

```bash
cd ~/avaliadorprompt.com.br
git pull origin main

# Backend
cd backend
source ../venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart avaliador-api

# Frontend
cd ../frontend
npm install
npm run build

# Reinicie o Nginx se necessário
sudo systemctl restart nginx
```

## 8. Segurança Adicional

1. Configure o firewall conforme recomendado
2. Implemente backups regulares do banco de dados
3. Monitore regularmente os logs de acesso para detectar atividades suspeitas
