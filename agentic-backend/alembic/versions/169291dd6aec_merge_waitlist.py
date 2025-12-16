"""merge_waitlist

Revision ID: 169291dd6aec
Revises: 556cc8b2acde, waitlist_001
Create Date: 2025-12-12 13:21:44.150700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '169291dd6aec'
down_revision: Union[str, Sequence[str], None] = ('556cc8b2acde', 'waitlist_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
