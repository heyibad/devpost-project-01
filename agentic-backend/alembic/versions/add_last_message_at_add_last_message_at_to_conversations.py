"""add_last_message_at_to_conversations

Revision ID: add_last_message_at
Revises: fca1930d8a4d
Create Date: 2025-11-18

"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = "add_last_message_at"
down_revision = "fca1930d8a4d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add last_message_at column to conversations table
    op.add_column(
        "conversations", sa.Column("last_message_at", sa.DateTime(), nullable=True)
    )

    # Create index on last_message_at for efficient sorting
    op.create_index(
        "ix_conversations_last_message_at",
        "conversations",
        ["last_message_at"],
        unique=False,
    )

    # Backfill existing conversations with their latest message timestamp
    # This ensures existing data has proper timestamps
    op.execute(
        """
        UPDATE conversations
        SET last_message_at = (
            SELECT MAX(created_at)
            FROM messages
            WHERE messages.conversation_id = conversations.id
        )
        WHERE EXISTS (
            SELECT 1
            FROM messages
            WHERE messages.conversation_id = conversations.id
        )
    """
    )


def downgrade() -> None:
    # Remove index
    op.drop_index("ix_conversations_last_message_at", table_name="conversations")

    # Remove column
    op.drop_column("conversations", "last_message_at")
