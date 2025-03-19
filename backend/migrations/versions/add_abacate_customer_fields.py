"""Adiciona campos relacionados ao AbacatePay no model User

Revision ID: add_abacate_customer_fields
Revises: initial_migration
Create Date: 2023-03-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_abacate_customer_fields'
down_revision = 'initial_migration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adiciona as novas colunas à tabela de usuários
    op.add_column('users', sa.Column('abacate_customer_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('phone', sa.String(20), nullable=True))
    op.add_column('users', sa.Column('tax_id', sa.String(20), nullable=True))


def downgrade() -> None:
    # Remove as colunas adicionadas
    op.drop_column('users', 'abacate_customer_id')
    op.drop_column('users', 'phone')
    op.drop_column('users', 'tax_id') 