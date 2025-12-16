"""merge heads

Revision ID: 4ce138b63426
Revises: 902506a98b4a, a5479e200e4a
Create Date: 2025-11-14 20:27:53.326321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ce138b63426'
down_revision: Union[str, Sequence[str], None] = ('902506a98b4a', 'a5479e200e4a')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
