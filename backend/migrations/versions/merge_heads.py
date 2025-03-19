"""Migração para mesclar os dois heads

Revision ID: merge_heads
Revises: add_products_table, add_subscription_table
Create Date: 2023-03-20 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_heads'
down_revision = ('add_products_table', 'add_subscription_table')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Não precisa fazer nada, apenas mesclar os heads
    pass


def downgrade() -> None:
    # Não precisa fazer nada
    pass 