"""merge_heads

Revision ID: 556cc8b2acde
Revises: 87229900a69d, add_last_message_at
Create Date: 2025-11-18 15:19:27.985259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '556cc8b2acde'
down_revision: Union[str, Sequence[str], None] = ('87229900a69d', 'add_last_message_at')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
