from fastapi import APIRouter, Depends, HTTPException, status
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

@router.post("/contact", status_code=status.HTTP_200_OK)
async def send_contact_email(form_data: ContactForm) -> Dict[str, Any]:
    """
    Envia um email com os dados do formulário de contato para ribeitemp@gmail.com
    """
    try:
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
        
        # Conectar ao servidor SMTP e enviar o email
        if EMAIL_PORT == 465:
            # Conexão segura SSL
            server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
        else:
            # Conexão padrão com STARTTLS
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
            server.starttls()
            
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, "ribeitemp@gmail.com", message.as_string())
        server.quit()
        
        logger.info(f"Email de contato enviado - De: {form_data.email}, Nome: {form_data.name}")
        
        return {
            "success": True,
            "message": "Mensagem enviada com sucesso!"
        }
        
    except Exception as e:
        logger.error(f"Erro ao enviar email de contato: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao enviar mensagem. Por favor, tente novamente mais tarde."
        ) 