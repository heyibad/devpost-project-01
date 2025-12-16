"""add_tenant_primary_architecture

Complete database schema for Tenant-primary multi-tenant architecture.

Revision ID: 79ef2a14f0df
Revises: None (fresh start)
Create Date: 2025-11-03 21:54:19.575879

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel



# revision identifiers, used by Alembic.
revision: str = "79ef2a14f0df"
down_revision: Union[str, Sequence[str], None] = None  # First migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create complete tenant-primary schema from scratch."""

    # 1. Create Tenants table (Primary authentication entity)
    op.create_table(
        "tenants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column(
            "is_email_verified", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column("email_verified_at", sa.DateTime(), nullable=True),
        sa.Column("oauth_provider", sa.String(), nullable=True),
        sa.Column("oauth_id", sa.String(), nullable=True),
        sa.Column(
            "is_oauth_user", sa.Boolean(), server_default="false", nullable=False
        ),
        sa.Column("role", sa.String(), server_default="admin", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("avatar_url", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column(
            "subscription_plan", sa.String(), server_default="free", nullable=True
        ),
        sa.Column("max_users", sa.Integer(), server_default="5", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("idx_tenants_email", "tenants", ["email"], unique=True)
    op.create_index("idx_tenants_slug", "tenants", ["slug"], unique=True)
    op.create_index(
        "idx_tenants_oauth", "tenants", ["oauth_provider", "oauth_id"], unique=False
    )

    # 2. Create Users table (Sub-entities under Tenant, phone-based, no auth)
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("phone_no", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_no"),
    )
    op.create_index("idx_users_tenant_id", "users", ["tenant_id"], unique=False)
    op.create_index("idx_users_phone", "users", ["phone_no"], unique=True)

    # 3. Create Refresh Tokens table (Only for Tenants)
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), server_default="false", nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_refresh_tokens_tenant_id", "refresh_tokens", ["tenant_id"], unique=False
    )

    # 4. Create Conversations table (Tenant-level)
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("visibility", sa.String(), server_default="private", nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_conversations_tenant_id", "conversations", ["tenant_id"], unique=False
    )
    op.create_index(
        "idx_conversations_created_at", "conversations", ["created_at"], unique=False
    )

    # 5. Create Messages table (Tenant-level)
    op.create_table(
        "messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), server_default="completed", nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=True),
        sa.Column(
            "provider_meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_messages_conversation_id", "messages", ["conversation_id"], unique=False
    )
    op.create_index("idx_messages_tenant_id", "messages", ["tenant_id"], unique=False)
    op.create_index("idx_messages_created_at", "messages", ["created_at"], unique=False)

    # 6. Create User Conversations table (User-level)
    op.create_table(
        "user_conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_user_conversations_user_id",
        "user_conversations",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_user_conversations_created_at",
        "user_conversations",
        ["created_at"],
        unique=False,
    )

    # 7. Create User Messages table (User-level)
    op.create_table(
        "user_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), server_default="completed", nullable=False),
        sa.Column("tokens", sa.Integer(), nullable=True),
        sa.Column(
            "provider_meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["user_conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_user_messages_conversation_id",
        "user_messages",
        ["conversation_id"],
        unique=False,
    )
    op.create_index(
        "idx_user_messages_created_at", "user_messages", ["created_at"], unique=False
    )

    # 8. Create QuickBooks Connections table (Tenant-level)
    op.create_table(
        "quickbooks_connections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("access_token", sa.String(), nullable=False),
        sa.Column("refresh_token", sa.String(), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(), nullable=False),
        sa.Column("realm_id", sa.String(), nullable=False),
        sa.Column("company_name", sa.String(), nullable=True),
        sa.Column("company_country", sa.String(), nullable=True),
        sa.Column("company_currency", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("scopes", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_quickbooks_tenant_id",
        "quickbooks_connections",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "idx_quickbooks_realm_id", "quickbooks_connections", ["realm_id"], unique=False
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("quickbooks_connections")
    op.drop_table("user_messages")
    op.drop_table("user_conversations")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    op.drop_table("tenants")
