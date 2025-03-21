# Deployment Guide for Avaliador de Prompt IA via SFTP

Este guia descreve como fazer o deploy da aplicação Avaliador de Prompt IA na Hostinger usando apenas SFTP e o painel de controle.

## 1. Preparação do Frontend

1. **Compile o frontend localmente**:

```bash
cd /Users/educbank/Documents/Pompt\ AI\ Avaliator/frontend
npm install
npm run build
```

2. **Prepare o arquivo .htaccess para roteamento do React**:

Crie um arquivo `.htaccess` na pasta `build` com o seguinte conteúdo:

```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>

# Forçar HTTPS
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Cabeçalhos de segurança
<IfModule mod_headers.c>
  Header set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
  Header set X-Content-Type-Options "nosniff"
  Header set X-Frame-Options "SAMEORIGIN"
  Header set X-XSS-Protection "1; mode=block"
  Header set Referrer-Policy "strict-origin-when-cross-origin"
  Header set Content-Security-Policy "default-src 'self'; img-src 'self' data: https://cdn.avaliadorprompt.com.br; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; script-src 'self' 'unsafe-inline' https://cdn.avaliadorprompt.com.br; connect-src 'self' https://avaliadorprompt.com.br;"
</IfModule>
```

## 2. Preparação do Backend

1. **Prepare o .env para produção**:

Edite o arquivo `/Users/educbank/Documents/Pompt\ AI\ Avaliator/backend/.env.production` com as credenciais corretas.

2. **Crie um arquivo `passenger_wsgi.py`**:

Este arquivo é necessário para o Hostinger executar aplicações Python:

```python
# passenger_wsgi.py
import sys
import os

# Adicione o caminho do backend ao PYTHONPATH
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)

# Configure variáveis de ambiente
os.environ["ENV"] = "production"

# Carregue variáveis do arquivo .env.production
from dotenv import load_dotenv
dotenv_path = os.path.join(BACKEND_DIR, '.env.production')
load_dotenv(dotenv_path)

# Importe a aplicação FastAPI
from main import app

# Configure o aplicativo para WSGI
from fastapi.middleware.wsgi import WSGIMiddleware

# Crie uma aplicação WSGI a partir do aplicativo FastAPI
application = WSGIMiddleware(app)
```

3. **Crie um arquivo `.htaccess` para o backend**:

```apache
# Configurações para Python
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteRule ^(.*)$ /api/v1/$1 [QSA,L]
</IfModule>

# Cabeçalhos de segurança
<IfModule mod_headers.c>
  Header set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
  Header set X-Content-Type-Options "nosniff"
  Header set X-Frame-Options "SAMEORIGIN"
  Header set X-XSS-Protection "1; mode=block"
  Header set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>

# Limites de requisição para mitigar DDoS
<IfModule mod_reqtimeout.c>
  RequestReadTimeout header=20-40,MinRate=500
  RequestReadTimeout body=20,MinRate=500
</IfModule>
```

## 3. Deploy via SFTP

### Estrutura de Diretórios Recomendada

No Hostinger, você provavelmente terá um diretório principal para seu domínio (ex: `public_html`). Recomendamos a seguinte estrutura:

```
public_html/           # Diretório raiz - Frontend
  ├── index.html       # Arquivo principal do React
  ├── static/          # Arquivos estáticos React
  ├── .htaccess        # Regras de redirecionamento frontend
  └── api/             # Subdiretório para a API
       ├── passenger_wsgi.py  # Ponto de entrada para a aplicação Python
       ├── main.py            # Seu código backend existente
       ├── .env.production    # Variáveis de ambiente
       ├── .htaccess          # Configurações específicas da API
       ├── api/               # Seus módulos de API
       ├── services/          # Serviços
       └── ...                # Outros diretórios do backend
```

### Passos do Deploy

1. **Via SFTP (usando FileZilla ou similar)**:

   - Conecte-se ao seu servidor Hostinger usando credenciais SFTP
   - Carregue os arquivos do frontend compilado (pasta `build`) para o diretório raiz (`public_html`)
   - Crie uma pasta `api` e carregue os arquivos do backend para ela

2. **Configure Python no Painel de Controle da Hostinger**:

   - Acesse o painel de controle da Hostinger (hPanel)
   - Vá para a seção "Python"
   - Selecione a versão adequada do Python (3.9+ recomendado)
   - Defina o diretório da aplicação como `/api`
   - Defina o script de entrada como `passenger_wsgi.py`
   - Ative o ambiente Python

3. **Configurar o Banco de Dados**:

   - Use o painel de controle para criar um banco de dados MySQL
   - Atualize as credenciais no arquivo `.env.production`
   - Use a interface phpMyAdmin para importar o esquema inicial (se necessário)

## 4. Verificações Pós-Deploy

1. **Acesse seu site** em `https://avaliadorprompt.com.br`
2. **Verifique logs** através do painel de controle da Hostinger
3. **Teste endpoints da API** em `https://avaliadorprompt.com.br/api/...`

## 5. Segurança Adicional no Painel de Controle

1. **Ative o Firewall** na seção de segurança do painel da Hostinger
2. **Configure os backups regulares** do banco de dados
3. **Ative o ModSecurity** para proteção de aplicativos web
4. **Verifique se HTTPS** está corretamente configurado
5. **Configure limites de taxa** se disponível no seu plano

## 6. Atualizações Futuras

Para atualizar a aplicação:

1. Faça as alterações localmente
2. Para o frontend: execute `npm run build` e carregue os novos arquivos
3. Para o backend: carregue os arquivos alterados via SFTP
4. Reinicie a aplicação Python pelo painel de controle da Hostinger
