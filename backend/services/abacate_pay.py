import os
import requests
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações AbacatePay
GATEWAY_URL = os.getenv("GATEWAY_URL", "https://api.abacatepay.com/v1")
GATEWAY_SECRET_KEY = os.getenv("GATEWAY_SECRET_KEY")

class AbacatePayClient:
    """
    Cliente para integração com a API AbacatePay
    """
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or GATEWAY_SECRET_KEY
        self.base_url = base_url or GATEWAY_URL
        
        if not self.api_key:
            raise ValueError("AbacatePay API key is required")
        
        if not self.base_url:
            raise ValueError("AbacatePay base URL is required")
            
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
    
    def create_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria um cliente no AbacatePay
        
        Args:
            data: Dicionário com dados do cliente contendo:
                 - name: Nome completo do cliente
                 - cellphone: Celular do cliente
                 - email: E-mail do cliente
                 - taxId: CPF ou CNPJ do cliente
            
        Returns:
            Dict com a resposta da API
        """
        endpoint = f"{self.base_url}/customer/create"
        
        # Certifica-se de que os campos obrigatórios estão presentes
        required_fields = ["name", "cellphone", "email", "taxId"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Campo obrigatório ausente: {field}")
        
        # Faz a requisição para a API
        response = requests.post(endpoint, json=data, headers=self.headers)
        
        # Verifica a resposta
        if response.status_code != 200:
            error_detail = response.json().get("detail", str(response.text)) if response.headers.get("content-type") == "application/json" else str(response.text)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erro ao criar cliente no AbacatePay: {error_detail}"
            )
            
        return response.json()
    
    def create_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria uma cobrança no AbacatePay
        
        Args:
            data: Dicionário com dados da cobrança contendo:
                 - frequency: Tipo de frequência (ONE_TIME)
                 - methods: Lista de métodos de pagamento (PIX)
                 - products: Lista de produtos
                 - returnUrl: URL para redirecionamento em caso de cancelamento
                 - completionUrl: URL para redirecionamento após pagamento
                 - customerId: ID do cliente (opcional)
                 - customer: Dados do cliente (opcional)
            
        Returns:
            Dict com a resposta da API
        """
        endpoint = f"{self.base_url}/billing/create"
        
        # Certifica-se de que os campos obrigatórios estão presentes
        required_fields = ["frequency", "methods", "products", "returnUrl", "completionUrl"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Campo obrigatório ausente: {field}")
        
        # Verifica se pelo menos um produto foi informado
        if not data.get("products") or len(data["products"]) < 1:
            raise ValueError("Pelo menos um produto deve ser informado")
        
        # Verifica se customerId ou customer foi fornecido
        if "customerId" not in data and "customer" not in data:
            raise ValueError("Ou customerId ou customer deve ser fornecido")
        
        # Faz a requisição para a API
        response = requests.post(endpoint, json=data, headers=self.headers)
        
        # Verifica a resposta
        if response.status_code != 200:
            error_detail = response.json().get("detail", str(response.text)) if response.headers.get("content-type") == "application/json" else str(response.text)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erro ao criar cobrança no AbacatePay: {error_detail}"
            )
            
        return response.json()
    
    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Obtém informações de um pagamento específico
        
        Args:
            payment_id: ID do pagamento no AbacatePay
            
        Returns:
            Dict com a resposta da API
        """
        endpoint = f"{self.base_url}/billing/{payment_id}"
        response = requests.get(endpoint, headers=self.headers)
        
        if response.status_code != 200:
            error_detail = response.json().get("detail", str(response.text)) if response.headers.get("content-type") == "application/json" else str(response.text)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Erro ao obter pagamento no AbacatePay: {error_detail}"
            )
            
        return response.json()
    
    def generate_checkout_url(self, payment_data: Dict[str, Any]) -> str:
        """
        Gera URL de checkout para pagamento criando uma nova cobrança
        
        Args:
            payment_data: Dados completos para criar a cobrança
            
        Returns:
            URL de checkout
        """
        # Cria o pagamento
        payment_response = self.create_payment(payment_data)
        
        # Extrai a URL de checkout
        if "checkout_url" not in payment_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL de checkout não disponível para este pagamento"
            )
            
        return payment_response["checkout_url"] 