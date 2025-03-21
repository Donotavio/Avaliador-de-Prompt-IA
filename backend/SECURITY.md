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

## Gestão de Sessões e JWT

### Tokens JWT Seguros

O sistema implementa um mecanismo robusto de autenticação e gestão de sessões baseado em tokens JWT:

- **Expiração em Curto Prazo**: Os tokens de acesso expiram após 60 minutos, reduzindo a janela de oportunidade para ataques.
- **Sistema de Refresh Token**: Tokens de refresh com validade de 7 dias permitem a renovação da sessão sem necessidade de nova autenticação.
- **Rotação de Chaves**: As chaves de assinatura JWT são rotacionadas automaticamente a cada 30 dias.
- **Key ID (kid)**: Cada token inclui um identificador de chave, permitindo a validação com a chave correta mesmo após rotação.
- **Armazenamento Seguro**: As chaves são armazenadas em formato JSON em uma localização segura, acessível apenas pelo processo da aplicação.

### Controle de Sessões

O sistema oferece controle detalhado de sessões ativas:

- **Múltiplas Sessões**: Suporte para até 5 sessões simultâneas por usuário.
- **Rastreamento de Uso**: Cada sessão registra dados como IP, user agent, data de criação e expiração.
- **Revogação de Tokens**: Endpoints para logout de uma única sessão ou todas as sessões ativas.
- **Visualização de Sessões**: Os usuários podem ver e gerenciar suas sessões ativas.

### Proteção Contra Ataques de Força Bruta

Mecanismos implementados para proteger contra tentativas de invasão:

- **Contador de Falhas**: Rastreamento do número de tentativas de login malsucedidas.
- **Bloqueio Temporário**: Após 5 tentativas falhas, a conta é bloqueada por 15 minutos.
- **Mensagens de Erro Genéricas**: As mensagens de erro não revelam se o email ou a senha estão incorretos.

### Atualizações de Segurança

Para manter a segurança do sistema:

1. Verifique regularmente as chaves JWT em `data/jwt_keys.json`.
2. Execute a migração do Alembic para atualizar o banco de dados: `alembic upgrade head`.
3. Monitore o arquivo de log para identificar tentativas de login suspeitas ou bloqueios de conta.

## Prevenção contra Injeção SQL

A API incorpora múltiplas camadas de proteção contra ataques de injeção SQL:

### Sistema ORM

- **SQLAlchemy ORM**: Utilizamos o SQLAlchemy ORM para a maioria das operações de banco de dados, o que fornece proteção automática contra injeção SQL através de consultas parametrizadas.

### Consultas Parametrizadas

Para consultas SQL diretas, utilizamos:

- **Parâmetros Nomeados**: Todas as consultas SQL diretas usam parâmetros nomeados (`text("SELECT * FROM users WHERE id = :user_id")`) em vez de concatenação de strings.
- **Validação de Entrada**: Nomes de tabelas e colunas são validados através de padrões regex para permitir apenas caracteres seguros.

### Sistema de Validação para SQL Bruto

Implementamos um sistema de validação adicional:

- **Detecção de Padrões Maliciosos**: Consultas SQL são verificadas contra padrões potencialmente maliciosos como comandos múltiplos, comentários SQL e tentativas de UNION.
- **Logging de Segurança**: Tentativas suspeitas são registradas para análise posterior.

### Segurança em Migrações

- **Validação em Alembic**: As migrações do Alembic são protegidas por um sistema que verifica a segurança das consultas antes da execução.
- **Fallback Seguro**: Se a validação falhar para migrações legítimas, um sistema de fallback é usado com aviso em log.

### Boas Práticas

Ao desenvolver, siga estas diretrizes:

1. **Sempre use o ORM** quando possível para operações CRUD.
2. Para consultas complexas ou otimizadas, **use o módulo `utils.sql_security`**.
3. **Nunca concatene strings** para construir consultas SQL.
4. **Valide todas as entradas do usuário** antes de usá-las em consultas.

### Exemplo de Uso Seguro

```python
# Em vez de:
result = connection.execute(f"SELECT * FROM users WHERE email = '{email}'")  # INSEGURO!

# Use:
from utils.sql_security import safe_execute
result = safe_execute(connection, "SELECT * FROM users WHERE email = :email", {"email": email}) 
```

## Prevenção contra XSS em Emails

A aplicação implementa sanitização rigorosa de conteúdo HTML para prevenir vulnerabilidades XSS (Cross-Site Scripting) em emails:

### Sanitização de HTML

- **Biblioteca Bleach**: Utilizamos a biblioteca Bleach para sanitizar todo o conteúdo HTML antes de enviar emails.
- **Lista de Tags Permitidas**: Apenas um conjunto restrito de tags HTML é permitido (a, p, b, i, etc.), removendo qualquer tag potencialmente perigosa.
- **Atributos Filtrados**: Apenas atributos seguros são permitidos em cada tag, evitando atributos como onclick, onerror, etc.
- **Validação de Links**: URLs são validados para garantir que apontem apenas para domínios confiáveis.

### Proteções Adicionais

- **Verificação Dupla**: Além da sanitização principal, uma verificação secundária detecta padrões de XSS que possam ter passado pelo filtro inicial.
- **Fallback Seguro**: Em caso de detecção de conteúdo potencialmente malicioso, todo o HTML é removido e apenas texto puro é enviado.
- **Templates Seguros**: Utilizamos templates pré-definidos para emails, minimizando o risco de injeção de código malicioso.

### Validação de Links de Recuperação

Os links de recuperação de senha passam por validações específicas:

- **Validação de Formato**: O formato da URL é verificado através de expressões regulares.
- **Domínios Restritos**: Apenas domínios específicos são permitidos nos links (avaliadorprompt.com.br, localhost).
- **Logging de Segurança**: Tentativas de incluir links maliciosos são registradas para análise.

### Exemplo de Uso

Para enviar emails com conteúdo HTML seguro, utilize as funções do módulo `utils.email_security`:

```python
from utils.email_security import sanitize_html, create_safe_email_template

# Sanitizar conteúdo HTML
safe_content = sanitize_html(html_input)

# Ou criar um template completo seguro
email_body = create_safe_email_template(
    title="Título do Email",
    header="Cabeçalho do Email",
    main_content="<p>Conteúdo principal do email</p>"
)
```

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

## Hashing de Senhas e Autenticação

### Implementação segura de hash de senha

O sistema utiliza o algoritmo bcrypt para hash de senhas, considerado seguro para este propósito. A configuração inclui:

- **Algoritmo**: bcrypt (padrão da indústria)
- **Rounds**: 12 (configurável via `bcrypt__rounds`)
- **Versão**: 2b (versão compatível e segura)
- **Tratamento de erros**: Erros no processo de hash são tratados de forma adequada, sem fallbacks inseguros

Para garantir a segurança:
- Não há mecanismos de fallback inseguros para o hash de senha
- Erros de criptografia são registrados e propagados adequadamente
- Qualquer falha no sistema de hash resultará em erro explícito, em vez de comprometer a segurança

### Proteção contra ataques de força bruta

O sistema implementa proteções contra ataques de força bruta:

- Bloqueio de conta após 5 tentativas falhas de login (15 minutos)
- Rastreamento de IPs suspeitos
- Limites de sessões ativas por usuário (máximo 5)
- Registro detalhado de tentativas de login em logs seguros