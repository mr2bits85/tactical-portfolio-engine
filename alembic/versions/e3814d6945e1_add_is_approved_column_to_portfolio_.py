"""Add is_approved column to portfolio_snapshots

Revision ID: e3814d6945e1
Revises: 
Create Date: 2026-06-30 10:23:08.866883

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3814d6945e1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_approved column to portfolio_snapshots table
    op.add_column('portfolio_snapshots', sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove is_approved column from portfolio_snapshots table
    op.drop_column('portfolio_snapshots', 'is_approved')
