"""Adiciona campos de endereço e método de pagamento ao usuário

Revision ID: add_user_address_fields
Revises: merge_heads
Create Date: 2023-04-01 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_address_fields'
down_revision = 'merge_heads'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adicionar campos de endereço e método de pagamento à tabela de usuários
    op.add_column('users', sa.Column('address_street', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('address_number', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('address_complement', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('address_neighborhood', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('address_city', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('address_state', sa.String(2), nullable=True))
    op.add_column('users', sa.Column('address_postal_code', sa.String(10), nullable=True))
    op.add_column('users', sa.Column('address_country', sa.String(2), nullable=True, server_default='BR'))
    op.add_column('users', sa.Column('preferred_payment_method', sa.String(20), nullable=True))


def downgrade() -> None:
    # Remover campos adicionados
    op.drop_column('users', 'address_street')
    op.drop_column('users', 'address_number')
    op.drop_column('users', 'address_complement')
    op.drop_column('users', 'address_neighborhood')
    op.drop_column('users', 'address_city')
    op.drop_column('users', 'address_state')
    op.drop_column('users', 'address_postal_code')
    op.drop_column('users', 'address_country')
    op.drop_column('users', 'preferred_payment_method') 