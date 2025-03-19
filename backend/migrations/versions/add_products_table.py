"""Adiciona tabela de produtos para o AbacatePay

Revision ID: add_products_table
Revises: add_abacate_customer_fields
Create Date: 2023-03-20 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_products_table'
down_revision = 'add_abacate_customer_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cria a tabela de produtos
    op.create_table(
        'products',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('external_id', sa.String(100), unique=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('price_in_cents', sa.Integer, nullable=False),
        sa.Column('active', sa.Boolean, default=True),
        sa.Column('recurrence_period_days', sa.Integer, default=30),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Adiciona o índice para pesquisas por external_id
    op.create_index('idx_product_external_id', 'products', ['external_id'])
    
    # Insere o produto Premium padrão
    op.execute(
        """
        INSERT INTO products (id, external_id, name, description, price_in_cents, active, recurrence_period_days)
        VALUES (UUID(), 'premium-plan', 'Assinatura Premium', 'Acesso ilimitado à avaliação de prompts por 30 dias', 4990, 1, 30)
        """
    )


def downgrade() -> None:
    # Remove a tabela de produtos
    op.drop_table('products') 