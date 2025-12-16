"""add_waitlist_table

Revision ID: waitlist_001
Revises: fix_user_composite_key
Create Date: 2025-01-16 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "waitlist_001"
down_revision: Union[str, Sequence[str], None] = "fix_user_composite_key"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create waitlist table and add is_waitlist_approved and is_admin to tenants."""
    # Create waitlist table
    op.create_table(
        "waitlist",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by", sa.String(length=255), nullable=True),
        sa.Column("message", sa.String(length=1000), nullable=True),
        sa.Column("use_case", sa.String(length=500), nullable=True),
        sa.Column("business_type", sa.String(length=200), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("admin_notes", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index for tenant lookup
    op.create_index(
        op.f("ix_waitlist_tenant_id"),
        "waitlist",
        ["tenant_id"],
        unique=True,  # One waitlist entry per tenant
    )

    # Create index for approval status queries (admin view)
    op.create_index(
        "ix_waitlist_approval_status",
        "waitlist",
        ["is_approved", "created_at"],
        unique=False,
    )

    # Add is_waitlist_approved column to tenants table
    op.add_column(
        "tenants",
        sa.Column(
            "is_waitlist_approved", sa.Boolean(), nullable=False, server_default="false"
        ),
    )

    # Add is_admin column to tenants table
    op.add_column(
        "tenants",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    """Remove waitlist table and is_waitlist_approved, is_admin from tenants."""
    # Remove columns from tenants
    op.drop_column("tenants", "is_admin")
    op.drop_column("tenants", "is_waitlist_approved")

    # Drop indexes
    op.drop_index("ix_waitlist_approval_status", table_name="waitlist")
    op.drop_index(op.f("ix_waitlist_tenant_id"), table_name="waitlist")

    # Drop waitlist table
    op.drop_table("waitlist")
