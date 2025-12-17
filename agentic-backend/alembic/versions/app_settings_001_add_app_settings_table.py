"""Add app_settings table for global settings

Revision ID: app_settings_001
Revises: 169291dd6aec
Create Date: 2025-01-01 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "app_settings_001"
down_revision: Union[str, Sequence[str], None] = "169291dd6aec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("waitlist_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Insert default row
    op.execute(
        "INSERT INTO app_settings (id, waitlist_enabled) VALUES (1, true)"
    )


def downgrade() -> None:
    op.drop_table("app_settings")
