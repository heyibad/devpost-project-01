"""add_google_sheets_connection_table

Revision ID: google_sheets_v1
Revises: 79ef2a14f0df
Create Date: 2025-11-09

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "google_sheets_v1"
down_revision = "79ef2a14f0df"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create google_sheets_connections table
    op.create_table(
        "google_sheets_connections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("access_token", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("refresh_token", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(), nullable=False),
        sa.Column(
            "inventory_workbook_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column(
            "inventory_worksheet_name",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        ),
        sa.Column(
            "orders_workbook_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column(
            "orders_worksheet_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("scopes", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index(
        op.f("ix_google_sheets_connections_tenant_id"),
        "google_sheets_connections",
        ["tenant_id"],
        unique=True,
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        op.f("ix_google_sheets_connections_tenant_id"),
        table_name="google_sheets_connections",
    )

    # Drop table
    op.drop_table("google_sheets_connections")
