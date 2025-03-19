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
                 - methods: Lista de métodos de pagamento
                 - products: Lista de produtos
                 - returnUrl: URL para redirecionamento em caso de cancelamento
                 - completionUrl: URL para redirecionamento após pagamento
                 - customer: Dados do cliente
            
        Returns:
            Dict com a resposta da API
        """
        endpoint = f"{self.base_url}/billing/create"
        
        # Preparação e validação dos dados
        try:
            # Certifica-se de que os campos obrigatórios estão presentes
            required_fields = ["frequency", "methods", "products", "returnUrl", "completionUrl", "customer"]
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                error_msg = f"Campos obrigatórios ausentes: {', '.join(missing_fields)}"
                print(error_msg)
                return {"error": error_msg}
            
            # Verifica dados do cliente
            if "customer" in data:
                if "email" not in data["customer"]:
                    error_msg = "O campo 'email' é obrigatório no objeto customer"
                    print(error_msg)
                    return {"error": error_msg}
                
                # Verifica se o email é válido
                email = data["customer"].get("email", "")
                if not email or "@" not in email:
                    error_msg = f"Email inválido no objeto customer: {email}"
                    print(error_msg)
                    return {"error": error_msg}
            
            # Verifica produtos
            if not data.get("products") or len(data["products"]) < 1:
                error_msg = "Pelo menos um produto deve ser informado"
                print(error_msg)
                return {"error": error_msg}
            
            # Log dos dados finais sendo enviados
            print(f"Dados do pagamento a serem enviados para AbacatePay: {data}")
            
            # Faz a requisição para a API
            response = requests.post(endpoint, json=data, headers=self.headers)
            
            # Verifica a resposta e loga para debug
            print(f"AbacatePay Response: Status={response.status_code}, Headers={response.headers}, Data={response.text}")
            
            # Verifica a resposta
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", str(response.text))
                    if error_data.get("message"):
                        error_message = error_data.get("message")
                    error_detail = f"Erro ao criar cobrança no AbacatePay: {error_message}"
                except:
                    error_detail = f"Erro ao criar cobrança no AbacatePay: {str(response.text)}"
                    
                print(f"Erro na resposta: {error_detail}")
                return {"error": error_detail}
            
            try:
                # Tenta extrair os dados da resposta
                response_data = response.json()
                
                # Verifica se há erros na resposta
                if response_data.get("error"):
                    error_message = response_data["error"].get("message", "Erro desconhecido")
                    print(f"Erro nos dados de resposta: {error_message}")
                    return {"error": f"Erro do AbacatePay: {error_message}"}
                
                # Extrai os dados relevantes
                data = response_data.get("data", {})
                
                # Formata a resposta para o padrão esperado pela aplicação
                formatted_response = {
                    "id": data.get("id", ""),
                    "checkout_url": data.get("url", ""),
                    "status": data.get("status", "PENDING"),
                    "customer": data.get("customer", {})
                }
                
                print(f"Resposta formatada: {formatted_response}")
                return formatted_response
            except Exception as e:
                error_msg = f"Erro ao processar resposta da API: {str(e)}"
                print(error_msg)
                # Tenta retornar pelo menos a URL de checkout, se possível
                try:
                    return {"checkout_url": response.json().get("data", {}).get("url", "")}
                except:
                    return {"error": error_msg}
        
        except Exception as e:
            error_msg = f"Erro ao preparar dados para pagamento: {str(e)}"
            print(error_msg)
            return {"error": error_msg}
    
    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Obtém informações de um pagamento no AbacatePay
        
        Args:
            payment_id: ID do pagamento no AbacatePay
            
        Returns:
            Dict com a resposta da API contendo as informações do pagamento
        """
        # Primeiro, tenta o endpoint baseado no prefixo do ID
        if payment_id.startswith('bill_'):
            primary_endpoint = f"{self.base_url}/invoices/{payment_id}"
            backup_endpoint = f"{self.base_url}/bills/{payment_id}"
        else:
            primary_endpoint = f"{self.base_url}/bills/{payment_id}"
            backup_endpoint = f"{self.base_url}/invoices/{payment_id}"
        
        try:
            # Faz a requisição para a API
            response = requests.get(primary_endpoint, headers=self.headers)
            
            # Verifica a resposta e loga para debug
            print(f"AbacatePay Payment Details Response: Status={response.status_code}, Headers={response.headers}, Data={response.text}")
            
            # Se retornou 404, tenta o endpoint alternativo
            if response.status_code == 404:
                print(f"Tentando endpoint alternativo: {backup_endpoint}")
                response = requests.get(backup_endpoint, headers=self.headers)
                print(f"AbacatePay Alternative Endpoint Response: Status={response.status_code}, Headers={response.headers}, Data={response.text}")
            
            # Verifica se a resposta foi bem-sucedida
            if response.status_code != 200:
                error_message = str(response.text)
                try:
                    error_data = response.json()
                    if error_data.get("error"):
                        error_message = error_data["error"].get("message", error_message)
                except:
                    pass
                    
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Erro ao obter pagamento no AbacatePay: {error_message}"
                )
                
            # Extrai os dados da resposta
            response_data = response.json()
            
            # Verifica se há erros na resposta
            if response_data.get("error"):
                error_message = response_data["error"].get("message", "Erro desconhecido")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Erro do AbacatePay: {error_message}"
                )
            
            # Extrai os dados relevantes
            data = response_data.get("data", {})
            
            # Extrai e formata as informações relevantes para cada método de pagamento
            payment_method = data.get("methods", [])[0] if data.get("methods") else ""
            
            # Cria a estrutura base com os dados do pagamento
            payment_info = {
                "id": data.get("id", ""),
                "status": data.get("status", "PENDING"),
                "method": payment_method,
                "amount": data.get("amount", 0),
                "created_at": data.get("createdAt", ""),
                "updated_at": data.get("updatedAt", "")
            }
            
            # Verificar o qrCode no formato específico da API
            if payment_method == "PIX" and "pix" in data:
                pix_data = data.get("pix", {})
                payment_info["qr_code_url"] = pix_data.get("qrCodeUrl", "")
                payment_info["qr_code_text"] = pix_data.get("qrCodeText", "")
                
            # Se o método é boleto, obtém as informações específicas
            elif payment_method == "BOLETO" and "boleto" in data:
                boleto_data = data.get("boleto", {})
                payment_info["boleto_url"] = boleto_data.get("url", "")
                payment_info["boleto_code"] = boleto_data.get("barCode", "")
            
            return payment_info
            
        except Exception as e:
            # Captura qualquer erro e levanta uma exceção HTTP
            print(f"Erro ao processar detalhes do pagamento: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao obter pagamento: {str(e)}"
            )
    
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