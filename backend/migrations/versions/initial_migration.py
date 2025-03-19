"""Initial migration for users and subscriptions

Revision ID: initial_migration
Revises: 
Create Date: 2023-03-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cria a tabela de usuários
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('email', sa.String(255), unique=True, index=True),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Cria a tabela de assinaturas
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('plan_type', sa.String(50), nullable=False, default='premium'),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), default='BRL'),
        sa.Column('abacate_payment_id', sa.String(255), nullable=True),
        sa.Column('abacate_customer_id', sa.String(255), nullable=True),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Cria índices para melhorar a performance de consultas
    op.create_index(op.f('ix_subscriptions_user_id'), 'subscriptions', ['user_id'], unique=False)
    op.create_index(op.f('ix_subscriptions_status'), 'subscriptions', ['status'], unique=False)
    op.create_index(op.f('ix_subscriptions_abacate_payment_id'), 'subscriptions', ['abacate_payment_id'], unique=True)


def downgrade() -> None:
    # Remove as tabelas na ordem reversa de criação
    op.drop_table('subscriptions')
    op.drop_table('users') 