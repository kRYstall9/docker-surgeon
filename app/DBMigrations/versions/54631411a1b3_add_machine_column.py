"""add machine column

Revision ID: 54631411a1b3
Revises: 2a3ad493a301
Create Date: 2026-07-01 01:58:33.700569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '54631411a1b3'
down_revision: Union[str, Sequence[str], None] = '2a3ad493a301'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "crashedcontainers",
        sa.Column('machine', sa.String(100), nullable=True)
    )

    op.execute(
        """
        UPDATE 
            crashedcontainers
        SET 
            machine = 'Server'
        WHERE 
            machine IS NULL
        """
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column(
        "crashedcontainers",
        'machine'
    )
