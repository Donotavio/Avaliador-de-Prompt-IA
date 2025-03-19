from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Body
from sqlalchemy.orm import Session
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from services.database import get_db
from models.user import User
from models.product import Product
from models.subscription import Subscription
from schemas.subscription_schema import SubscriptionCreate, Subscription as SubscriptionSchema
from services.auth import get_current_user
from services.abacate_pay import AbacatePayClient

router = APIRouter(prefix="/payments", tags=["payments"])

# Instância do cliente AbacatePay
abacate_client = AbacatePayClient()

class UserPaymentData(BaseModel):
    taxId: str
    cellphone: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postalCode: Optional[str] = None

@router.post("/create", response_model=Dict[str, Any])
async def create_payment(
    subscription_data: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Cria um pagamento para assinatura premium
    
    Args:
        subscription_data: Dados da assinatura com informações de produto e do usuário
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Returns:
        Objeto com dados de confirmação do pagamento e URL de checkout
    """
    # Verifica se o usuário já tem assinatura ativa
    active_subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()
    
    if active_subscription and active_subscription.is_active():
        return {
            "message": "Assinatura já está ativa",
            "subscription_id": active_subscription.id,
            "status": active_subscription.status
        }
    
    try:
        # Extrair dados do corpo da requisição
        product_id = subscription_data.get("product_id")
        user_data = subscription_data.get("user_data", {})
        payment_method = subscription_data.get("payment_method", "PIX")
        
        # Validar método de pagamento
        valid_methods = ["PIX", "CREDIT_CARD", "BOLETO"]
        if payment_method not in valid_methods:
            payment_method = "PIX"  # Padrão para fallback
        
        # Se não informou produto, busca o produto premium padrão
        if not product_id:
            product = db.query(Product).filter(
                Product.external_id == "premium-plan",
                Product.active == True
            ).first()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Produto premium não encontrado"
                )
        else:
            # Busca o produto específico
            product = db.query(Product).filter(
                Product.id == product_id,
                Product.active == True
            ).first()
            
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Produto não encontrado"
                )
        
        # Atualiza dados adicionais do usuário se fornecidos
        updated_user = False
        if user_data:
            # Dados básicos
            if "taxId" in user_data and not current_user.tax_id:
                current_user.tax_id = user_data["taxId"]
                updated_user = True
                
            if "cellphone" in user_data and not current_user.phone:
                current_user.phone = user_data["cellphone"]
                updated_user = True
            
            # Dados de endereço - sempre atualizar para garantir informações mais recentes
            if "address" in user_data:
                current_user.address_street = user_data["address"]
                updated_user = True
                
            if "addressNumber" in user_data:
                current_user.address_number = user_data["addressNumber"]
                updated_user = True
                
            if "complement" in user_data:
                current_user.address_complement = user_data["complement"]
                updated_user = True
                
            if "neighborhood" in user_data:
                current_user.address_neighborhood = user_data["neighborhood"]
                updated_user = True
                
            if "city" in user_data:
                current_user.address_city = user_data["city"]
                updated_user = True
                
            if "state" in user_data:
                current_user.address_state = user_data["state"]
                updated_user = True
                
            if "postalCode" in user_data:
                current_user.address_postal_code = user_data["postalCode"]
                updated_user = True
            
            # Método de pagamento preferido
            current_user.preferred_payment_method = payment_method
            updated_user = True
                
            if updated_user:
                db.commit()
                print(f"Dados de usuário atualizados: {current_user.id}")
        
        # Extrai dados adicionais do usuário
        address_number = user_data.get('addressNumber', '')
        complement = user_data.get('complement', '')
        neighborhood = user_data.get('neighborhood', '')
        
        # Prepara os dados para a API AbacatePay
        base_url = "http://localhost:3000"
        
        # Dados para a criação da cobrança
        payment_data = {
            "frequency": "ONE_TIME",
            "methods": ["PIX"],  # Método de pagamento PIX é o único suportado atualmente pelo AbacatePay
            "products": [
                {
                    "externalId": product.external_id,
                    "name": product.name,
                    "description": product.description or "Assinatura Premium",
                    "quantity": 1,
                    "price": product.price_in_cents
                }
            ],
            "returnUrl": f"{base_url}/payment-cancel",
            "completionUrl": f"{base_url}/payment-success",
            "webhookUrl": f"{base_url}/api/payments/webhook",
            "devMode": True  # Ative para testes
        }
        
        # Se o usuário já tiver um ID de cliente no AbacatePay, usamos ele
        if current_user.abacate_customer_id:
            payment_data["customer"] = {
                "id": current_user.abacate_customer_id,
                "name": current_user.full_name,
                "email": current_user.email.strip(),  # Garante que não haja espaços no email
                "cellphone": current_user.phone or user_data.get("cellphone", "11999999999"),
                "taxId": current_user.tax_id or user_data.get("taxId", "00000000191")  # CPF válido para teste
            }
        else:
            # Caso contrário, enviamos os dados do cliente para criar junto com o pagamento
            payment_data["customer"] = {
                "name": current_user.full_name,
                "email": current_user.email.strip(),  # Garante que não haja espaços no email
                "taxId": current_user.tax_id or user_data.get("taxId", "00000000191"),  # CPF válido para teste
                "cellphone": current_user.phone or user_data.get("cellphone", "11999999999")
            }
            
            # Adiciona dados de endereço somente se houver rua/cidade
            if user_data.get("address") or user_data.get("city"):
                payment_data["customer"]["address"] = {
                    "street": user_data.get("address", ""),
                    "number": address_number,
                    "complement": complement,
                    "neighborhood": neighborhood,
                    "city": user_data.get("city", ""),
                    "state": user_data.get("state", ""),
                    "country": "BR",
                    "zipCode": user_data.get("postalCode", "")
                }
        
        # Cria a cobrança usando o novo método da API
        print(f"Tentando criar pagamento para usuário: {current_user.id}")
        payment_response = abacate_client.create_payment(payment_data)
        
        # Verifica se a resposta contém erro
        if "error" in payment_response:
            error_message = payment_response.get("error", "Erro desconhecido")
            print(f"Erro retornado pelo AbacatePay: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        # Verifica se a resposta contém a URL de checkout
        if not payment_response or "checkout_url" not in payment_response:
            error_msg = "Erro ao gerar URL de pagamento"
            if payment_response:
                error_msg += f": {payment_response.get('error', '')}"
            print(error_msg)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
        
        print(f"Resposta do pagamento: {payment_response}")
        
        # Se o cliente foi criado durante a cobrança e não tínhamos o ID, salvamos agora
        if "customer" in payment_response and not current_user.abacate_customer_id:
            customer_id = payment_response["customer"].get("id", "")
            if customer_id:
                current_user.abacate_customer_id = customer_id
                db.commit()
                print(f"ID do cliente salvo: {customer_id}")
        
        # Cria uma nova assinatura no banco de dados
        new_subscription = Subscription(
            user_id=current_user.id,
            status="pending",  # Status inicial é pendente até confirmação de pagamento
            plan_type="premium",
            amount=product.price,
            currency="BRL",
            payment_method=subscription_data["payment_method"],
            abacate_payment_id=payment_response.get("id", ""),
            abacate_customer_id=current_user.abacate_customer_id
        )
        
        db.add(new_subscription)
        db.commit()
        db.refresh(new_subscription)
        
        return {
            "message": "Pagamento criado com sucesso",
            "subscription_id": new_subscription.id,
            "checkout_url": payment_response["checkout_url"],
            "status": new_subscription.status
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao criar pagamento: {str(e)}"
        )

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def payment_webhook(request: Request, db: Session = Depends(get_db)) -> Response:
    """
    Webhook para receber notificações de pagamento do AbacatePay
    """
    try:
        # Recebe dados do webhook
        payload = await request.json()
        
        # Log para depuração
        print(f"Webhook recebido: {payload}")
        
        # Verifica o tipo de evento
        event_type = payload.get("type")
        
        if event_type == "billing.paid":
            # Pagamento foi confirmado
            billing_id = payload.get("data", {}).get("id")
            
            # Busca a assinatura correspondente
            subscription = db.query(Subscription).filter(
                Subscription.abacate_payment_id == billing_id
            ).first()
            
            if subscription:
                # Atualiza status da assinatura
                subscription.status = "active"
                subscription.start_date = datetime.now()
                subscription.end_date = datetime.now() + timedelta(days=30)  # 30 dias de assinatura
                
                # Também podemos ativar o premium para o usuário no sistema de uso
                from services.usage_manager import usage_manager
                try:
                    usage_manager.activate_premium(subscription.user_id)
                except Exception as e:
                    print(f"Erro ao ativar premium no usage_manager: {e}")
                
                db.commit()
                print(f"Assinatura {subscription.id} ativada com sucesso")
        
        elif event_type == "billing.expired" or event_type == "billing.canceled":
            # Pagamento expirou ou foi cancelado
            billing_id = payload.get("data", {}).get("id")
            
            # Busca a assinatura correspondente
            subscription = db.query(Subscription).filter(
                Subscription.abacate_payment_id == billing_id
            ).first()
            
            if subscription:
                # Atualiza status da assinatura
                subscription.status = "expired" if event_type == "billing.expired" else "cancelled"
                
                db.commit()
                print(f"Assinatura {subscription.id} marcada como {subscription.status}")
        
        # Retorna resposta de confirmação para o webhook
        return Response(status_code=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"Erro ao processar webhook: {e}")
        # Ainda retornamos 200 para que a AbacatePay saiba que recebemos a notificação
        return Response(status_code=status.HTTP_200_OK)

@router.get("/status", response_model=Dict[str, Any])
async def check_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Verifica o status da assinatura do usuário
    """
    # Busca a assinatura mais recente do usuário
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).order_by(Subscription.created_at.desc()).first()
    
    if not subscription:
        return {
            "has_subscription": False,
            "status": None,
            "message": "Nenhuma assinatura encontrada"
        }
    
    # Verifica se a assinatura está ativa
    is_active = subscription.is_active()
    
    return {
        "has_subscription": True,
        "is_active": is_active,
        "status": subscription.status,
        "plan_type": subscription.plan_type,
        "start_date": subscription.start_date,
        "end_date": subscription.end_date,
        "abacate_payment_id": subscription.abacate_payment_id,
        "subscription": {
            "id": subscription.id,
            "status": subscription.status,
            "abacate_payment_id": subscription.abacate_payment_id,
            "abacate_customer_id": subscription.abacate_customer_id,
            "payment_method": subscription.payment_method
        },
        "message": "Assinatura ativa" if is_active else "Assinatura inativa ou expirada"
    }

@router.get("/details/{payment_id}", response_model=Dict[str, Any])
async def payment_details(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Obtém detalhes de um pagamento específico, incluindo QR code para PIX ou código de boleto
    
    Args:
        payment_id: ID do pagamento
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Returns:
        Objeto com detalhes do pagamento específicos para o método utilizado
    """
    try:
        # Procurar a assinatura no banco
        subscription = db.query(Subscription).filter(
            Subscription.abacate_payment_id == payment_id,
            Subscription.user_id == current_user.id
        ).first()
        
        if not subscription:
            # Como pode ser um novo pagamento, tente encontrar a mais recente
            subscription = db.query(Subscription).filter(
                Subscription.user_id == current_user.id
            ).order_by(Subscription.created_at.desc()).first()
            
            if not subscription:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Nenhuma assinatura encontrada para este usuário"
                )
        
        # Obter detalhes do pagamento do AbacatePay
        try:
            payment_details = abacate_client.get_payment(payment_id)
            
            # Construir resposta de acordo com o método de pagamento
            payment_method = payment_details.get("method", "")
            payment_status = payment_details.get("status", "pending")
            
            response_data = {
                "id": payment_id,
                "status": payment_status,
                "method": payment_method,
                "amount": subscription.amount,
                "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
            }
            
            # Adicionar dados específicos para cada método de pagamento
            if payment_method == "PIX":
                response_data["qr_code_url"] = payment_details.get("qr_code_url", "")
                response_data["qr_code_text"] = payment_details.get("qr_code_text", "")
            elif payment_method == "BOLETO":
                response_data["boleto_url"] = payment_details.get("boleto_url", "")
                response_data["boleto_code"] = payment_details.get("boleto_code", "")
            
            return response_data
            
        except Exception as e:
            # Se não conseguiu obter detalhes, retornar pelo menos os dados básicos
            print(f"Erro ao processar detalhes do pagamento: {str(e)}")
            
            # Retornar a URL de checkout direta do AbacatePay
            checkout_base_url = abacate_client.base_url.replace('/v1', '')
            checkout_url = f"{checkout_base_url}/pay/{payment_id}"
            
            return {
                "id": payment_id,
                "status": subscription.status,
                "method": subscription.payment_method if hasattr(subscription, 'payment_method') else "PIX",
                "amount": subscription.amount,
                "created_at": subscription.created_at.isoformat() if subscription.created_at else None,
                "checkout_url": checkout_url
            }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao obter detalhes do pagamento: {str(e)}"
        )

@router.get("/status/{payment_id}", response_model=Dict[str, Any])
async def payment_status(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Verifica o status atual de um pagamento específico
    
    Args:
        payment_id: ID do pagamento
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Returns:
        Objeto com o status atual do pagamento
    """
    try:
        # Procurar a assinatura no banco
        subscription = db.query(Subscription).filter(
            Subscription.abacate_payment_id == payment_id,
            Subscription.user_id == current_user.id
        ).first()
        
        if not subscription:
            # Como pode ser um novo pagamento, tente encontrar a mais recente
            subscription = db.query(Subscription).filter(
                Subscription.user_id == current_user.id
            ).order_by(Subscription.created_at.desc()).first()
            
            if not subscription:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Nenhuma assinatura encontrada para este usuário"
                )
        
        # Obter detalhes atualizados do pagamento do AbacatePay
        try:
            payment_details = abacate_client.get_payment(payment_id)
            payment_status = payment_details.get("status", "pending")
            
            # Se o status mudou para pago, atualize a assinatura
            if payment_status.upper() == "PAID" and subscription.status != "active":
                subscription.status = "active"
                subscription.start_date = datetime.now()
                subscription.end_date = datetime.now() + timedelta(days=30)  # 30 dias de assinatura
                
                # Também podemos ativar o premium para o usuário no sistema de uso
                from services.usage_manager import usage_manager
                try:
                    usage_manager.activate_premium(subscription.user_id)
                except Exception as e:
                    print(f"Erro ao ativar premium no usage_manager: {e}")
                
                db.commit()
                print(f"Assinatura {subscription.id} ativada com sucesso via verificação de status")
                
            return {
                "id": payment_id,
                "status": payment_status,
                "subscription_id": subscription.id,
                "is_active": subscription.is_active(),
                "method": payment_details.get("method", "PIX")
            }
        except Exception as e:
            # Se não conseguir obter o status da API, use o status atual da assinatura
            print(f"Erro ao consultar status na API: {str(e)}")
            
            # Gera URL de checkout para redirecionamento
            checkout_base_url = abacate_client.base_url.replace('/v1', '')
            checkout_url = f"{checkout_base_url}/pay/{payment_id}"
            
            return {
                "id": payment_id,
                "status": subscription.status,
                "subscription_id": subscription.id,
                "is_active": subscription.is_active(),
                "method": subscription.payment_method if hasattr(subscription, 'payment_method') else "PIX",
                "checkout_url": checkout_url
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao verificar status do pagamento: {str(e)}"
        )

@router.post("/verify-payment/{payment_id}", response_model=Dict[str, Any])
async def verify_payment(
    payment_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Verifica e ativa manualmente o status de um pagamento.
    Útil quando o webhook não foi recebido ou processado corretamente.
    
    Args:
        payment_id: ID do pagamento no AbacatePay
        request: Objeto Request
        current_user: Usuário autenticado
        db: Sessão do banco de dados
        
    Returns:
        Objeto com o resultado da verificação
    """
    try:
        print(f"Verificando manualmente pagamento {payment_id} para usuário {current_user.id}")
        
        # Busca a assinatura no banco de dados
        subscription = db.query(Subscription).filter(
            Subscription.abacate_payment_id == payment_id,
            Subscription.user_id == current_user.id
        ).first()
        
        if not subscription:
            # Como pode ser um novo pagamento, tente encontrar a mais recente
            subscription = db.query(Subscription).filter(
                Subscription.user_id == current_user.id
            ).order_by(Subscription.created_at.desc()).first()
            
            if not subscription:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Nenhuma assinatura encontrada para este usuário"
                )
        
        # Verifica se a solicitação pede para forçar ativação (vindo da tela de sucesso do AbacatePay)
        force_success = "success" in request.query_params and request.query_params["success"].lower() == "true"
        
        # Se forçar sucesso ou viemos de uma URL de sucesso, ativamos a assinatura
        if force_success or "success" in request.query_params or request.headers.get("Referer", "").endswith("/payment-success"):
            # Atualiza a assinatura
            if subscription.status != "active":
                subscription.status = "active"
                subscription.start_date = datetime.now()
                subscription.end_date = datetime.now() + timedelta(days=30)
                
                # Ativa o premium para o usuário
                from services.usage_manager import usage_manager
                try:
                    usage_manager.activate_premium(subscription.user_id)
                except Exception as e:
                    print(f"Erro ao ativar premium: {e}")
                
                db.commit()
                print(f"Assinatura {subscription.id} ativada manualmente por redirecionamento à página de sucesso")
            
            return {
                "success": True,
                "status": "ACTIVE",
                "message": "Assinatura ativada com sucesso",
                "subscription_id": subscription.id
            }
        
        # Verifica o status do pagamento no AbacatePay, se não foi forçado
        try:
            payment_details = abacate_client.get_payment(payment_id)
            payment_status = payment_details.get("status", "").upper()
            
            print(f"Status do pagamento no AbacatePay: {payment_status}")
            
            # Se o pagamento estiver confirmado, ativa a assinatura
            if payment_status == "PAID" or payment_status == "CONFIRMED":
                # Atualiza a assinatura
                if subscription.status != "active":
                    subscription.status = "active"
                    subscription.start_date = datetime.now()
                    subscription.end_date = datetime.now() + timedelta(days=30)
                    
                    # Ativa o premium para o usuário
                    from services.usage_manager import usage_manager
                    try:
                        usage_manager.activate_premium(subscription.user_id)
                    except Exception as e:
                        print(f"Erro ao ativar premium: {e}")
                    
                    db.commit()
                    print(f"Assinatura {subscription.id} ativada manualmente com sucesso")
                
                return {
                    "success": True,
                    "status": "ACTIVE",
                    "message": "Pagamento confirmado e assinatura ativada",
                    "subscription_id": subscription.id
                }
            
            return {
                "success": False,
                "status": payment_status,
                "message": f"Pagamento ainda não confirmado: {payment_status}",
                "subscription_id": subscription.id
            }
            
        except Exception as e:
            print(f"Erro ao verificar status no AbacatePay: {str(e)}")
            
            # Tenta fazer uma verificação alternativa
            # Se o usuário está retornando da página de sucesso do AbacatePay,
            # podemos assumir que o pagamento foi confirmado
            if "success" in request.query_params or request.headers.get("Referer", "").endswith("/payment-success"):
                # Atualiza a assinatura
                if subscription.status != "active":
                    subscription.status = "active"
                    subscription.start_date = datetime.now()
                    subscription.end_date = datetime.now() + timedelta(days=30)
                    
                    # Ativa o premium para o usuário
                    from services.usage_manager import usage_manager
                    try:
                        usage_manager.activate_premium(subscription.user_id)
                    except Exception as e:
                        print(f"Erro ao ativar premium: {e}")
                    
                    db.commit()
                    print(f"Assinatura {subscription.id} ativada manualmente por presunção de sucesso")
                
                return {
                    "success": True,
                    "status": "ACTIVE",
                    "message": "Assinatura ativada (pagamento presumido como confirmado)",
                    "subscription_id": subscription.id
                }
            
            # Se não, retorna falha
            return {
                "success": False,
                "status": "UNKNOWN",
                "message": f"Não foi possível verificar o status do pagamento: {str(e)}",
                "subscription_id": subscription.id
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao verificar pagamento: {str(e)}"
        ) 