from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List

from services.database import get_db
from models.user import User
from models.product import Product
from schemas.product_schema import ProductCreate, ProductUpdate, Product as ProductSchema
from services.auth import get_current_admin_user

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=List[ProductSchema])
async def list_products(
    active_only: bool = True,
    db: Session = Depends(get_db)
) -> Any:
    """
    Lista todos os produtos disponíveis.
    
    Args:
        active_only: Se True, retorna apenas produtos ativos
        db: Sessão do banco de dados
        
    Returns:
        Lista de produtos
    """
    query = db.query(Product)
    
    if active_only:
        query = query.filter(Product.active == True)
        
    products = query.all()
    return products

@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(
    product_id: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Obtém informações de um produto específico
    
    Args:
        product_id: ID do produto
        db: Sessão do banco de dados
        
    Returns:
        Detalhes do produto
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
        
    return product

@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """
    Cria um novo produto (apenas administradores)
    
    Args:
        product_data: Dados do produto
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
        
    Returns:
        Produto criado
    """
    # Verifica se já existe um produto com o mesmo external_id
    db_product = db.query(Product).filter(Product.external_id == product_data.external_id).first()
    
    if db_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Produto com external_id '{product_data.external_id}' já existe"
        )
    
    # Cria o produto
    new_product = Product(
        external_id=product_data.external_id,
        name=product_data.name,
        description=product_data.description,
        price_in_cents=product_data.price_in_cents,
        active=product_data.active,
        recurrence_period_days=product_data.recurrence_period_days
    )
    
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    return new_product

@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> Any:
    """
    Atualiza um produto existente (apenas administradores)
    
    Args:
        product_id: ID do produto
        product_data: Dados atualizados do produto
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
        
    Returns:
        Produto atualizado
    """
    # Busca o produto
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    # Atualiza os campos
    for field, value in product_data.dict(exclude_unset=True).items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    return product 