"""
Testes de unidade para o módulo de segurança de email.
"""

import unittest
import sys
import os
import logging

# Adiciona o diretório raiz ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.email_security import (
    sanitize_html,
    create_safe_email_template,
    sanitize_recovery_link
)

# Desabilita logs durante os testes
logging.disable(logging.CRITICAL)

class TestEmailSecurity(unittest.TestCase):
    """Testes para o módulo de segurança de email."""
    
    def test_sanitize_html_scripts(self):
        """Testa remoção de scripts no HTML."""
        html = '<script>alert("XSS")</script><p>Conteúdo legítimo</p>'
        sanitized = sanitize_html(html)
        self.assertNotIn('<script>', sanitized)
        self.assertIn('<p>Conteúdo legítimo</p>', sanitized)
    
    def test_sanitize_html_malicious_attributes(self):
        """Testa remoção de atributos maliciosos."""
        html = '<a href="javascript:alert(\'XSS\')" onclick="alert(\'XSS\')">Link</a>'
        sanitized = sanitize_html(html)
        self.assertNotIn('javascript:', sanitized)
        self.assertNotIn('onclick', sanitized)
        self.assertIn('<a', sanitized)
        self.assertIn('Link', sanitized)
    
    def test_sanitize_html_css_injection(self):
        """Testa proteção contra injeção CSS."""
        html = '<div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: url(\'javascript:alert(1)\')">Teste</div>'
        sanitized = sanitize_html(html)
        self.assertNotIn('javascript:', sanitized)
        self.assertIn('<div', sanitized)
        self.assertIn('Teste', sanitized)
    
    def test_sanitize_html_nested_attack(self):
        """Testa ataques XSS aninhados."""
        html = '<img src="x" onerror="alert(\'XSS\')" /><div><script>document.write(\'<img src=x onerror=alert("XSS")>\')</script></div>'
        sanitized = sanitize_html(html)
        self.assertNotIn('<script>', sanitized)
        self.assertNotIn('onerror', sanitized)
    
    def test_create_safe_email_template(self):
        """Testa criação de template de email seguro."""
        title = "<script>alert('XSS')</script>Título Seguro"
        header = "Cabeçalho <iframe src='javascript:alert(\"XSS\")'></iframe>"
        content = "<p>Conteúdo</p><img src='x' onerror='alert(\"XSS\")' />"
        
        template = create_safe_email_template(title, header, content)
        
        self.assertNotIn('<script>', template)
        self.assertNotIn('<iframe', template)
        self.assertNotIn('onerror', template)
        self.assertIn('Título Seguro', template)
        self.assertIn('Cabeçalho', template)
        self.assertIn('<p>Conteúdo</p>', template)
    
    def test_sanitize_recovery_link_valid(self):
        """Testa validação de link de recuperação válido."""
        valid_link = "https://www.avaliadorprompt.com.br/reset-password?token=abc123"
        sanitized = sanitize_recovery_link(valid_link)
        self.assertEqual(valid_link, sanitized)
        
        valid_link_localhost = "http://localhost:3000/reset-password?token=abc123"
        sanitized_localhost = sanitize_recovery_link(valid_link_localhost)
        self.assertEqual(valid_link_localhost, sanitized_localhost)
    
    def test_sanitize_recovery_link_invalid(self):
        """Testa rejeição de links de recuperação inválidos."""
        invalid_links = [
            "javascript:alert('XSS')",
            "data:text/html,<script>alert('XSS')</script>",
            "https://malicious-site.com/reset?token=abc",
            "http://fake-avaliadorprompt.com.br/reset"
        ]
        
        for link in invalid_links:
            sanitized = sanitize_recovery_link(link)
            self.assertEqual("", sanitized)

if __name__ == "__main__":
    unittest.main() 