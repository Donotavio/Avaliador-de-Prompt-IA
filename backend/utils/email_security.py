"""
Utilitários para garantir segurança no envio de emails e prevenir XSS.
"""

import bleach
import re
import logging
from typing import List, Dict, Any, Optional
from bleach.css_sanitizer import CSSSanitizer

logger = logging.getLogger(__name__)

# Tags HTML permitidas por padrão nos emails
DEFAULT_ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'br', 'code',
    'div', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i',
    'li', 'ol', 'p', 'pre', 'span', 'strong', 'table', 'tbody',
    'td', 'th', 'thead', 'tr', 'u', 'ul'
]

# Atributos HTML permitidos por padrão
DEFAULT_ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'style', 'class'],
    'abbr': ['title'],
    'acronym': ['title'],
    'div': ['style', 'class'],
    'h1': ['style', 'class'],
    'h2': ['style', 'class'],
    'h3': ['style', 'class'],
    'h4': ['style', 'class'],
    'h5': ['style', 'class'],
    'h6': ['style', 'class'],
    'p': ['style', 'class'],
    'span': ['style', 'class'],
    'td': ['colspan', 'rowspan', 'style'],
    'th': ['colspan', 'rowspan', 'style'],
    'tr': ['style'],
    'img': ['src', 'alt', 'title', 'style', 'class', 'width', 'height'],
    '*': ['style', 'class']
}

# Estilos CSS permitidos
DEFAULT_ALLOWED_STYLES = [
    'color', 'background-color', 'font-size', 'font-weight', 'font-family',
    'text-align', 'text-decoration', 'border', 'border-radius', 'padding',
    'margin', 'display', 'width', 'height', 'max-width', 'max-height'
]

# Protocolos permitidos nas URLs
DEFAULT_ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

def sanitize_html(
    html_content: str,
    allowed_tags: Optional[List[str]] = None,
    allowed_attributes: Optional[Dict[str, List[str]]] = None,
    allowed_protocols: Optional[List[str]] = None,
    allowed_styles: Optional[List[str]] = None
) -> str:
    """
    Sanitiza conteúdo HTML para prevenir ataques XSS.
    
    Args:
        html_content: O conteúdo HTML a ser sanitizado
        allowed_tags: Lista de tags HTML permitidas
        allowed_attributes: Dicionário de atributos permitidos para cada tag
        allowed_protocols: Lista de protocolos URL permitidos
        allowed_styles: Lista de propriedades CSS permitidas
        
    Returns:
        str: HTML sanitizado e seguro
    """
    # Verifica se foi fornecido, senão usa os padrões
    if allowed_tags is None:
        allowed_tags = DEFAULT_ALLOWED_TAGS
        
    if allowed_attributes is None:
        allowed_attributes = DEFAULT_ALLOWED_ATTRIBUTES
        
    if allowed_protocols is None:
        allowed_protocols = DEFAULT_ALLOWED_PROTOCOLS
        
    if allowed_styles is None:
        allowed_styles = DEFAULT_ALLOWED_STYLES
    
    try:
        # Configura o sanitizador CSS
        css_sanitizer = CSSSanitizer(allowed_css_properties=allowed_styles)
        
        # Utiliza Bleach para sanitizar o HTML
        sanitized_html = bleach.clean(
            html_content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            protocols=allowed_protocols,
            css_sanitizer=css_sanitizer,
            strip=True,
            strip_comments=True
        )
        
        # Verificação adicional para garantir que não existam scripts
        if re.search(r'<script|javascript:|data:|vbscript:|on\w+=', sanitized_html, re.IGNORECASE):
            logger.warning("XSS potencial detectado após sanitização. Removendo todo HTML.")
            sanitized_html = bleach.clean(html_content, tags=[], strip=True)
        
        return sanitized_html
    except Exception as e:
        logger.error(f"Erro durante sanitização de HTML: {str(e)}")
        # Em caso de erro, retorna texto puro (sem HTML)
        return bleach.clean(html_content, tags=[], strip=True)

def create_safe_email_template(
    title: str,
    header: str,
    main_content: str,
    footer: str = "Atenciosamente,<br>Equipe Prompt AI Evaluator"
) -> str:
    """
    Cria um template de email estruturado e sanitizado.
    
    Args:
        title: Título do email
        header: Conteúdo do cabeçalho
        main_content: Conteúdo principal
        footer: Texto do rodapé (opcional)
        
    Returns:
        str: Template HTML sanitizado
    """
    # Sanitiza todas as entradas
    safe_title = sanitize_html(title, allowed_tags=['b', 'i', 'strong', 'em'])
    safe_header = sanitize_html(header)
    safe_main_content = sanitize_html(main_content)
    safe_footer = sanitize_html(footer)
    
    # Cria o template básico com estilos inline
    email_template = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
        <div style="padding: 20px; background-color: #f8f8f8; border-bottom: 1px solid #ddd;">
            <h2>{safe_title}</h2>
            <p>{safe_header}</p>
        </div>
        <div style="padding: 20px;">
            {safe_main_content}
        </div>
        <div style="padding: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #777;">
            {safe_footer}
        </div>
    </body>
    </html>
    """
    
    return email_template

def sanitize_recovery_link(recovery_link: str) -> str:
    """
    Sanitiza um link de recuperação de senha para garantir que seja seguro.
    
    Args:
        recovery_link: Link de recuperação de senha
        
    Returns:
        str: Link sanitizado ou vazio se não for seguro
    """
    try:
        # Verificação contra protocolos maliciosos
        if re.search(r'^(javascript|data|vbscript):', recovery_link, re.IGNORECASE):
            logger.warning(f"Protocolo malicioso detectado em link: {recovery_link}")
            return ""
        
        # Domínios permitidos
        allowed_domains = [
            'avaliadorprompt.com.br', 
            'www.avaliadorprompt.com.br',
            'localhost'
        ]
        
        # Verifica se é link local especial (x-webdoc)
        if recovery_link.startswith('x-webdoc://'):
            logger.info(f"Link local especial detectado: {recovery_link}")
            return recovery_link
        
        # Verificação básica de URL para links web padrão - permite query params mais complexos
        url_pattern = r'^https?://[\w\.-]+(:\d+)?(/[\w\.-/~%&?=+_-]*)?$'
        if not re.match(url_pattern, recovery_link):
            logger.warning(f"Link de recuperação com formato inválido: {recovery_link}")
            return ""
        
        # Extrai o domínio da URL
        domain_match = re.search(r'https?://([\w\.-]+(?::\d+)?)', recovery_link)
        if not domain_match:
            logger.warning(f"Não foi possível extrair o domínio do link: {recovery_link}")
            return ""
        
        domain = domain_match.group(1).lower()
        domain_without_port = domain.split(':')[0]  # Remove a porta se existir
        
        # Verifica se é localhost (com ou sem porta)
        if domain_without_port == 'localhost':
            return recovery_link
        
        # Verifica se o domínio é um dos permitidos
        for allowed in allowed_domains:
            if domain_without_port == allowed or domain_without_port.endswith('.' + allowed):
                return recovery_link
            
        logger.warning(f"Domínio não permitido no link de recuperação: {domain}")
        return ""
    except Exception as e:
        logger.error(f"Erro ao validar link de recuperação: {str(e)}")
        return "" 