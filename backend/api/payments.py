from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from typing import Any, Dict
from datetime import datetime, timedelta

from database import get_db
from models.user import User
from models.subscription import Subscription
from schemas.subscription_schema import SubscriptionCreate, Subscription as SubscriptionSchema
from services.auth import get_current_user
from services.abacate_pay import AbacatePayClient

router = APIRouter(prefix="/payments", tags=["payments"])

# Instância do cliente AbacatePay
abacate_client = AbacatePayClient()

@router.post("/create", response_model=Dict[str, Any])
async def create_payment(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Cria um pagamento para assinatura premium
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
    
    # Define valores padrão para o plano premium
    premium_plan_price = 4990  # 49.90 em centavos conforme exigido pela API
    
    try:
        # Prepara os dados para a API AbacatePay
        base_url = "https://prompt-avaliator.com"
        
        # Dados para a criação da cobrança
        payment_data = {
            "frequency": "ONE_TIME",
            "methods": ["PIX"],
            "products": [
                {
                    "externalId": f"premium-plan-{current_user.id}",
                    "name": "Assinatura Premium - Avaliador de Prompts IA",
                    "description": "Acesso ilimitado à avaliação de prompts por 30 dias",
                    "quantity": 1,
                    "price": premium_plan_price
                }
            ],
            "returnUrl": f"{base_url}/payment-cancel",
            "completionUrl": f"{base_url}/payment-success"
        }
        
        # Se o usuário já tiver um ID de cliente no AbacatePay, usamos ele
        if current_user.abacate_customer_id:
            payment_data["customerId"] = current_user.abacate_customer_id
        else:
            # Caso contrário, enviamos os dados do cliente para criar junto com o pagamento
            payment_data["customer"] = {
                "name": current_user.full_name,
                "email": current_user.email,
                "taxId": current_user.tax_id or "00000000000",  # CPF padrão se não tiver
                "cellphone": current_user.phone or "11999999999"  # Telefone padrão se não tiver
            }
        
        # Cria a cobrança usando o novo método da API
        payment_response = abacate_client.create_payment(payment_data)
        
        # Verifica se a resposta contém a URL de checkout
        if not payment_response or "checkout_url" not in payment_response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao gerar URL de pagamento"
            )
        
        # Se o cliente foi criado durante a cobrança e não tínhamos o ID, salvamos agora
        if "customer" in payment_response and not current_user.abacate_customer_id:
            current_user.abacate_customer_id = payment_response["customer"]["id"]
            db.commit()
        
        # Cria uma nova assinatura no banco de dados
        new_subscription = Subscription(
            user_id=current_user.id,
            status="pending",  # Status inicial é pendente até confirmação de pagamento
            plan_type=subscription_data.plan_type,
            amount=subscription_data.amount or premium_plan_price / 100,  # Convertemos de centavos para reais
            currency="BRL",
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
        "message": "Assinatura ativa" if is_active else "Assinatura inativa ou expirada"
    } 