#!/usr/bin/env python3
"""
Script para verificação periódica de segurança da aplicação.
Pode ser executado manualmente ou automaticamente através de um cron job.
"""

import os
import sys
import json
import logging
import requests
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
import argparse

# Adiciona diretório pai ao path para import relativo
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.security_tests import test_cors_configuration, verify_security_headers

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/security_checks.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("security_checker")

# Carrega configurações de ambiente
load_dotenv()

# Configurações de email
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "")
EMAIL_TO = os.getenv("EMAIL_TO", "contato@avaliadorprompt.com.br").split(",")

# Configurações padrão
PROD_API_URL = "https://avaliadorprompt.com.br/api"
DEV_API_URL = "http://localhost:8000/api"

# Domínios de produção
PROD_ALLOWED_ORIGINS = [
    "https://avaliadorprompt.com.br",
    "https://www.avaliadorprompt.com.br"
]

# Domínios de desenvolvimento
DEV_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5000"
]

# Origens que nunca devem ser permitidas (sempre testadas)
DISALLOWED_ORIGINS = [
    "http://attacker.com",
    "https://evil-site.org",
    "http://malicious-domain.net"
]

def is_production():
    """
    Verifica se estamos rodando em ambiente de produção.
    Tenta resolver o domínio de produção para determinar se é produção.
    """
    try:
        # Tenta resolver o domínio de produção
        socket.gethostbyname("avaliadorprompt.com.br")
        return True
    except:
        return False

def detect_environment(args):
    """
    Detecta o ambiente com base nos argumentos e na resolução DNS.
    """
    # Se o ambiente foi especificado via argumento, use-o
    if args.environment:
        env = args.environment.lower()
        if env in ['prod', 'production']:
            return "production", PROD_API_URL, PROD_ALLOWED_ORIGINS + DEV_ALLOWED_ORIGINS
        else:
            return "development", DEV_API_URL, DEV_ALLOWED_ORIGINS
    
    # Caso contrário, detecte automaticamente
    if is_production():
        return "production", PROD_API_URL, PROD_ALLOWED_ORIGINS + DEV_ALLOWED_ORIGINS
    else:
        return "development", DEV_API_URL, DEV_ALLOWED_ORIGINS

def send_security_alert(subject, message):
    """Envia um email de alerta de segurança"""
    if not all([EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_FROM]):
        logger.error("Configurações de email incompletas. Não foi possível enviar alerta.")
        return False
    
    try:
        for recipient in EMAIL_TO:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_FROM
            msg["To"] = recipient
            msg["Subject"] = f"[ALERTA DE SEGURANÇA] {subject}"
            
            # Corpo do email em formato HTML
            html_body = f"""
            <html>
            <body>
                <h2>Alerta de Segurança: {subject}</h2>
                <p>Foi detectado um possível problema de segurança na aplicação.</p>
                <h3>Detalhes:</h3>
                <pre>{message}</pre>
                <p>Data e hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Este é um alerta automático. Por favor, verifique a aplicação o mais rápido possível.</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, "html"))
            
            # Conecta ao servidor SMTP
            if EMAIL_PORT == 465:
                server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
            else:
                server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
                server.starttls()
                
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            
        logger.info(f"Alerta de segurança enviado para {', '.join(EMAIL_TO)}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar alerta de segurança: {str(e)}")
        return False

def can_connect_to_url(url):
    """Verifica se consegue conectar a uma URL"""
    try:
        response = requests.get(url, timeout=5)
        return True
    except:
        return False

def main():
    """Função principal para realizar as verificações de segurança"""
    # Configurar argumentos de linha de comando
    parser = argparse.ArgumentParser(description='Verificar segurança da aplicação')
    parser.add_argument('--env', '--environment', dest='environment', 
                        choices=['dev', 'development', 'prod', 'production'],
                        help='Especificar ambiente (dev/prod)')
    parser.add_argument('--url', dest='api_url', 
                        help='URL da API para testar')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Exibir mensagens detalhadas')
    
    args = parser.parse_args()
    
    # Detectar ambiente
    env_name, api_url, allowed_origins = detect_environment(args)
    
    # Sobrescrever URL se especificada via argumento
    if args.api_url:
        api_url = args.api_url
    
    logger.info(f"Iniciando verificação de segurança em ambiente: {env_name}")
    logger.info(f"URL da API: {api_url}")
    
    # Verificar se consegue se conectar à API
    if not can_connect_to_url(api_url):
        logger.error(f"Não foi possível conectar à API em {api_url}")
        logger.info("Tentando URL alternativa para ambiente de desenvolvimento...")
        
        # Se estamos em desenvolvimento e a API padrão não está disponível, tente a porta 8000
        if env_name == "development" and api_url != DEV_API_URL:
            api_url = DEV_API_URL
            if not can_connect_to_url(api_url):
                logger.error(f"Também não foi possível conectar à API em {api_url}")
                logger.error("A API não está acessível. Verifique se o servidor está em execução.")
                return 1
        else:
            logger.error("A API não está acessível. Verifique se o servidor está em execução.")
            return 1
    
    success = True
    
    # Testa configuração CORS
    logger.info("Verificando configuração CORS...")
    try:
        cors_results = test_cors_configuration(api_url, allowed_origins, DISALLOWED_ORIGINS)
        
        if not cors_results["success"]:
            logger.warning("Configuração CORS falhou na verificação!")
            if env_name == "production":
                send_security_alert(
                    "Problema na configuração CORS",
                    json.dumps(cors_results, indent=2)
                )
            success = False
        else:
            logger.info("Configuração CORS aprovada ✅")
    except Exception as e:
        logger.error(f"Erro ao verificar configuração CORS: {str(e)}")
        success = False
    
    # Verifica cabeçalhos de segurança
    logger.info("Verificando cabeçalhos de segurança...")
    try:
        headers_results = verify_security_headers(api_url)
        
        if not headers_results["success"]:
            logger.warning("Verificação de cabeçalhos de segurança falhou!")
            if env_name == "production":
                send_security_alert(
                    "Problema nos cabeçalhos de segurança",
                    json.dumps(headers_results, indent=2)
                )
            success = False
        else:
            logger.info("Cabeçalhos de segurança aprovados ✅")
    except Exception as e:
        logger.error(f"Erro ao verificar cabeçalhos de segurança: {str(e)}")
        success = False
    
    logger.info("Verificação de segurança concluída")
    
    # Exibe resultado final
    if success:
        logger.info(f"✅ Todos os testes de segurança passaram com sucesso em ambiente {env_name}!")
        return 0
    else:
        logger.warning(f"❌ Existem problemas de segurança em ambiente {env_name} que precisam ser corrigidos!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 