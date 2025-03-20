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
    # Primeiro verificamos se a tabela já existe
    conn = op.get_bind()
    
    # Usar uma query parametrizada
    result = conn.execute(
        text("SHOW TABLES LIKE :table_name"),
        {"table_name": 'subscriptions'}
    )
    
    # Se a tabela não existir, criamos
    if result.rowcount == 0:
        op.create_table('subscriptions',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('plan_type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True, server_default='BRL'),
        sa.Column('abacate_payment_id', sa.String(length=255), nullable=True),
        sa.Column('abacate_customer_id', sa.String(length=255), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        )
        
        # Cria um índice para user_id
        op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'], unique=False)
        
        # Cria índices para melhorar performance de queries
        op.create_index('idx_subscription_status', 'subscriptions', ['status'])
        op.create_index('idx_subscription_abacate_payment_id', 'subscriptions', ['abacate_payment_id'])
    
    print("Migração de assinaturas concluída!")


def downgrade() -> None:
    # Verifica se a tabela existe antes de tentar removê-la
    conn = op.get_bind()
    
    # Usar uma query parametrizada
    result = conn.execute(
        text("SHOW TABLES LIKE :table_name"),
        {"table_name": 'subscriptions'}
    )
    
    # Se a tabela existir, removemos
    if result.rowcount > 0:
        op.drop_index(op.f('ix_subscriptions_user_id'), table_name='subscriptions')
        op.drop_table('subscriptions') 