"""Adiciona tabela de assinaturas

Revision ID: add_subscription_table
Revises: add_abacate_customer_fields
Create Date: 2023-03-20 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'add_subscription_table'
down_revision = 'add_abacate_customer_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Verifica se a tabela já existe
    conn = op.get_bind()
    result = conn.execute(text("SHOW TABLES LIKE 'subscriptions'"))
    if not result.fetchone():
        # Cria a tabela de assinaturas apenas se ela não existir
        op.create_table(
            'subscriptions',
            sa.Column('id', sa.String(36), primary_key=True, index=True),
            sa.Column('user_id', sa.String(36), sa.ForeignKey("users.id"), nullable=False),
            sa.Column('status', sa.String(50), default="pending"),
            sa.Column('plan_type', sa.String(50), nullable=False, default="premium"),
            sa.Column('amount', sa.Float, nullable=False),
            sa.Column('currency', sa.String(3), default="BRL"),
            sa.Column('abacate_payment_id', sa.String(255), nullable=True),
            sa.Column('abacate_customer_id', sa.String(255), nullable=True),
            sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
        )
        
        # Cria índices para melhorar performance de queries
        op.create_index('idx_subscription_user_id', 'subscriptions', ['user_id'])
        op.create_index('idx_subscription_status', 'subscriptions', ['status'])
        op.create_index('idx_subscription_abacate_payment_id', 'subscriptions', ['abacate_payment_id'])
    
    print("Migração de assinaturas concluída!")


def downgrade() -> None:
    # Remove a tabela de assinaturas
    conn = op.get_bind()
    result = conn.execute(text("SHOW TABLES LIKE 'subscriptions'"))
    if result.fetchone():
        op.drop_table('subscriptions') 