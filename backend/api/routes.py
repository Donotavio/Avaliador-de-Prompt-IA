from fastapi import APIRouter, Depends, HTTPException, status, Request
from services.usage_manager import usage_manager
from config.settings import USAGE_LIMITS
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
import json
from pathlib import Path

# Configurações de email - as mesmas usadas em auth.py
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "no-reply@avaliadorprompt.com.br")

logger = logging.getLogger(__name__)

router = APIRouter()

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str

@router.get("/free/status/{user_id}")
async def get_free_status(user_id: str):
    """
    Verifica o status do usuário para avaliações gratuitas
    
    Returns:
        - Dict com status, limite e mensagem
    """
    user_usage = usage_manager.get_user_usage(user_id)
    can_use, message = user_usage.can_use_free()
    
    # Não incluir a mensagem na resposta se o usuário pode usar normalmente
    if can_use and not message:
        return {
            "status": can_use,
            "evaluation_count": user_usage.free_evaluations_count,
            "daily_limit": USAGE_LIMITS["free"]["daily_limit"]
        }
    
    return {
        "status": can_use,
        "message": message,
        "evaluation_count": user_usage.free_evaluations_count,
        "daily_limit": USAGE_LIMITS["free"]["daily_limit"]
    }

async def save_contact_to_file(form_data: ContactForm) -> bool:
    """
    Salva os dados do formulário de contato em um arquivo JSON como backup
    quando o envio por email falha.
    
    Args:
        form_data: Dados do formulário de contato
        
    Returns:
        bool: True se o arquivo foi salvo com sucesso, False caso contrário
    """
    try:
        # Criar o diretório de backup se não existir
        backup_dir = Path("/var/www/avaliadorprompt/backend/backups/contacts")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Gerar nome de arquivo único com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"contact_{timestamp}_{form_data.email.replace('@', '_at_')}.json"
        
        # Converter dados para JSON
        contact_data = {
            "name": form_data.name,
            "email": form_data.email,
            "message": form_data.message,
            "timestamp": datetime.now().isoformat()
        }
        
        # Salvar em arquivo
        with open(backup_file, "w") as f:
            json.dump(contact_data, f, indent=2)
            
        logger.info(f"Dados de contato salvos em arquivo de backup: {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar dados de contato em arquivo: {str(e)}")
        return False

@router.post("/contact", status_code=status.HTTP_200_OK)
async def send_contact_email(
    form_data: ContactForm,
    request: Request
) -> Dict[str, Any]:
    """
    Envia um email com os dados do formulário de contato para ribeitemp@gmail.com
    Esta rota não requer proteção CSRF.
    """
    try:
        # Registrar os dados recebidos (exceto a mensagem completa por questões de privacidade)
        logger.info(f"Tentativa de envio de formulário de contato - De: {form_data.email}, Nome: {form_data.name}")
        
        # Configurar o email
        subject = f"Novo contato pelo site - {form_data.name}"
        
        # Criar o conteúdo do email em HTML
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="padding: 20px; background-color: #f8f8f8; border-bottom: 1px solid #ddd;">
                <h2>Nova mensagem de contato</h2>
                <p>Recebido em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            </div>
            <div style="padding: 20px;">
                <p><strong>Nome:</strong> {form_data.name}</p>
                <p><strong>Email:</strong> {form_data.email}</p>
                <p><strong>Mensagem:</strong></p>
                <p style="background-color: #f9f9f9; padding: 10px; border-left: 3px solid #ccc;">{form_data.message}</p>
            </div>
            <div style="padding: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #777;">
                Enviado pelo formulário de contato do Avaliador de Prompt IA
            </div>
        </body>
        </html>
        """
        
        # Criar a mensagem MIME
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = EMAIL_FROM
        message["To"] = "ribeitemp@gmail.com"  # Email fixo para receber contatos
        
        # Anexar as partes HTML à mensagem
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Registrar informações de debug sobre a conexão SMTP
        logger.info(f"Tentando conexão SMTP - Host: {EMAIL_HOST}, Porta: {EMAIL_PORT}")
        logger.info(f"Usuário de email: {EMAIL_USER}")
        
        try:
            # Conectar ao servidor SMTP e enviar o email
            if EMAIL_PORT == 465:
                # Conexão segura SSL
                logger.info("Usando conexão SSL")
                server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, timeout=30)
            else:
                # Conexão padrão com STARTTLS
                logger.info("Usando conexão STARTTLS")
                server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=30)
                server.starttls()
            
            # Tentar autenticação
            logger.info("Tentando autenticação SMTP")
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            
            # Enviar email
            logger.info("Enviando email")
            server.sendmail(EMAIL_FROM, "ribeitemp@gmail.com", message.as_string())
            
            # Fechar conexão
            server.quit()
            logger.info("Email enviado com sucesso")
            
            return {
                "success": True,
                "message": "Mensagem enviada com sucesso!"
            }
        except smtplib.SMTPAuthenticationError as auth_error:
            logger.error(f"Erro de autenticação SMTP: {str(auth_error)}")
            
            # Tenta salvar os dados em arquivo como backup
            await save_contact_to_file(form_data)
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha na autenticação do servidor de email. Sua mensagem foi registrada e entraremos em contato assim que possível."
            )
        except smtplib.SMTPException as smtp_error:
            logger.error(f"Erro SMTP específico: {str(smtp_error)}")
            
            # Tenta salvar os dados em arquivo como backup
            await save_contact_to_file(form_data)
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro no servidor de email. Sua mensagem foi registrada e entraremos em contato assim que possível."
            )
        
    except Exception as e:
        logger.error(f"Erro ao processar envio de email de contato: {str(e)}")
        logger.exception("Detalhes completos do erro:")
        
        # Tenta salvar os dados em arquivo como backup
        saved = await save_contact_to_file(form_data)
        
        if saved:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao enviar mensagem, mas seus dados foram salvos. Entraremos em contato assim que possível."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao enviar mensagem. Por favor, tente novamente mais tarde ou entre em contato via contato@avaliadorprompt.com."
            ) 