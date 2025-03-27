"""add_email_verification_fields

Revision ID: ad3f45a61b22
Revises: add_subscription_table
Create Date: 2023-03-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ad3f45a61b22'
down_revision = 'add_subscription_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adiciona campos de verificação de e-mail
    op.add_column('users', sa.Column('is_email_verified', sa.Boolean(), nullable=True, server_default='0'))
    op.add_column('users', sa.Column('email_verification_token', sa.String(length=6), nullable=True))
    op.add_column('users', sa.Column('email_token_expires', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove campos de verificação de e-mail
    op.drop_column('users', 'is_email_verified')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_token_expires') 