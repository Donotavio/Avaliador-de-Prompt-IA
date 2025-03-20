# Documentação de Segurança - Avaliador de Prompts

Este documento descreve as medidas de segurança implementadas na aplicação Avaliador de Prompts, incluindo a configuração CORS segura, cabeçalhos HTTP de segurança e outras práticas recomendadas.

## Configuração CORS Segura

A aplicação implementa uma configuração CORS (Cross-Origin Resource Sharing) restritiva que segue as melhores práticas de segurança:

### Origens Permitidas

Apenas as seguintes origens são permitidas a acessar a API:

- `https://avaliadorprompt.com.br` (Produção)
- `https://www.avaliadorprompt.com.br` (Produção com www)
- `http://localhost:3000` (Desenvolvimento local frontend)
- `http://localhost:5000` (Ambiente de teste local)

### Métodos HTTP Permitidos

Apenas os seguintes métodos HTTP são permitidos:

- GET
- POST
- PUT
- DELETE

### Cabeçalhos Permitidos

Apenas os seguintes cabeçalhos são permitidos:

- Authorization
- Content-Type
- X-CSRF-Token

## Cabeçalhos de Segurança HTTP

A aplicação implementa os seguintes cabeçalhos de segurança em todas as respostas HTTP:

| Cabeçalho                   | Valor                                     | Propósito                                 |
|-----------------------------|-------------------------------------------|------------------------------------------|
| X-Frame-Options             | SAMEORIGIN                                | Previne ataques clickjacking              |
| X-Content-Type-Options      | nosniff                                   | Previne MIME type sniffing                |
| X-XSS-Protection            | 1; mode=block                             | Proteção XSS para navegadores antigos     |
| Strict-Transport-Security   | max-age=31536000; includeSubDomains      | Força HTTPS para todas as conexões        |
| Content-Security-Policy     | Múltiplas diretivas                       | Previne XSS e outras injeções de conteúdo |
| Referrer-Policy             | strict-origin-when-cross-origin           | Limita informações de referência          |

## Verificação Automática de Segurança

A aplicação inclui ferramentas para verificação automática da configuração de segurança:

### Executando Verificações Manuais

Para executar manualmente as verificações de segurança:

```bash
cd backend
python -m tools.security_checker
```

Ou usando o script diretamente:

```bash
cd backend
./tools.security_checker.py
```

### Configurando Verificações Automáticas

Para monitoramento contínuo, configure um cron job no servidor Hostinger:

```bash
# Verificar segurança diariamente às 3h da manhã
0 3 * * * cd /caminho/para/backend && ./tools/security_checker.py >> logs/security_cron.log 2>&1
```

### Alertas de Segurança

Quando uma verificação de segurança falha, o sistema:

1. Registra detalhes no arquivo de log `logs/security_checks.log`
2. Envia um email de alerta para o endereço configurado em `EMAIL_TO`

## Recomendações Adicionais para Hostinger

Ao implantar na Hostinger, siga estas recomendações adicionais:

1. Configure o `.htaccess` para reforçar HTTPS e adicionar camadas extras de segurança:

```apache
# Redirecionar para HTTPS
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Desativar listagem de diretórios
Options -Indexes

# Prevenir acesso a arquivos sensíveis
<FilesMatch "^\.">
    Order allow,deny
    Deny from all
</FilesMatch>

# Prevenir acesso a arquivos de configuração
<FilesMatch "\.(env|config|json|md|gitignore|htaccess|log|py[cod]|po|pot|ini)$">
    Order allow,deny
    Deny from all
</FilesMatch>
```

2. Configure um firewall no painel da Hostinger para limitar acessos indesejados.

3. Certifique-se de que o certificado SSL está configurado corretamente.

## Contato de Segurança

Para reportar problemas de segurança, entre em contato com a equipe através do email seguro:

- contato@avaliadorprompt.com.br 