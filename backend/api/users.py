from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List

from database import get_db
from models.user import User
from schemas.user_schema import User as UserSchema, UserUpdate
from services.auth import get_current_user, get_current_admin_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserSchema)
def read_current_user(current_user: User = Depends(get_current_user)) -> Any:
    """
    Obtém os dados do usuário atual
    """
    return current_user

@router.put("/me", response_model=UserSchema)
def update_current_user(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Atualiza os dados do usuário atual
    """
    # Atualiza os dados do usuário
    if user_data.email:
        # Verifica se o email já está em uso por outro usuário
        db_user = db.query(User).filter(User.email == user_data.email).first()
        if db_user and db_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já está em uso"
            )
        current_user.email = user_data.email
    
    if user_data.full_name:
        current_user.full_name = user_data.full_name
    
    if user_data.password:
        current_user.hashed_password = User.get_password_hash(user_data.password)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.get("", response_model=List[UserSchema])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
) -> Any:
    """
    Obtém todos os usuários (somente admin)
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserSchema)
def read_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user)
) -> Any:
    """
    Obtém os dados de um usuário específico (somente admin)
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
        
    return user 