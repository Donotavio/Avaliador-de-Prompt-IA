"""merge_email_verification_migration

Revision ID: b6d6a52c9d80
Revises: 958a5a05fca9, ad3f45a61b22
Create Date: 2025-03-27 16:49:59.619243

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6d6a52c9d80'
down_revision = ('958a5a05fca9', 'ad3f45a61b22')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass 