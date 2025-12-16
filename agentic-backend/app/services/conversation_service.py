"""Service for conversation operations with optimized queries."""

from typing import Optional
from uuid import UUID
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.message import Message


class ConversationService:
    """Optimized service for conversation operations."""

    @staticmethod
    async def get_conversations_for_tenant(
        db: AsyncSession,
        tenant_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """
        Get paginated list of conversations for a tenant.

        OPTIMIZED: Raw SQL query for maximum performance and correct sorting.
        SORTED BY: Last message created_at DESC (most recent message = top)
        Returns:
            Tuple of (conversations list as dicts, total count)
        """
        from sqlalchemy import text

        # Get total count
        count_result = await db.execute(
            text("SELECT COUNT(*) FROM conversations WHERE tenant_id = :tenant_id"),
            {"tenant_id": tenant_id},
        )
        total_count = count_result.scalar_one()

        # Optimized raw SQL query with proper sorting by last message
        query = text(
            """
            WITH last_messages AS (
                SELECT DISTINCT ON (conversation_id)
                    conversation_id,
                    content as last_content,
                    created_at as last_msg_time
                FROM messages
                ORDER BY conversation_id, created_at DESC
            ),
            message_counts AS (
                SELECT 
                    conversation_id,
                    COUNT(*) as msg_count
                FROM messages
                GROUP BY conversation_id
            )
            SELECT 
                c.id,
                c.title,
                c.created_at,
                lm.last_content,
                lm.last_msg_time,
                COALESCE(mc.msg_count, 0) as message_count
            FROM conversations c
            LEFT JOIN last_messages lm ON c.id = lm.conversation_id
            LEFT JOIN message_counts mc ON c.id = mc.conversation_id
            WHERE c.tenant_id = :tenant_id
            ORDER BY 
                lm.last_msg_time DESC NULLS LAST,
                c.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        )

        result = await db.execute(
            query, {"tenant_id": tenant_id, "limit": limit, "offset": offset}
        )
        rows = result.all()

        # Convert to list of dicts
        conversations = [
            {
                "id": str(row.id),
                "title": row.title,
                "created_at": row.created_at,
                "last_message_at": row.last_msg_time or row.created_at,
                "last_content": row.last_content,
                "message_count": row.message_count,
            }
            for row in rows
        ]

        return conversations, total_count

    @staticmethod
    async def get_conversation_with_messages(
        db: AsyncSession,
        conversation_id: UUID,
        tenant_id: UUID,
    ) -> Optional[Conversation]:
        """
        Get a single conversation with all its messages.

        Optimized with eager loading to avoid N+1 queries.
        """
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.tenant_id == tenant_id)
            .options(selectinload(Conversation.messages))
        )

        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        return conversation

    @staticmethod
    async def update_conversation_timestamp(
        db: AsyncSession,
        conversation_id: UUID,
    ) -> None:
        """
        Update last_message_at timestamp for a conversation.

        Called after each new message.
        """
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if conversation:
            conversation.last_message_at = datetime.utcnow()
            db.add(conversation)
            await db.flush()

    @staticmethod
    async def get_conversation_preview(
        db: AsyncSession,
        conversation_id: UUID,
        tenant_id: UUID,
    ) -> Optional[dict]:
        """
        Get conversation with preview (last message only).

        Used for list views to avoid loading all messages.
        """
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.tenant_id == tenant_id)
        )

        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            return None

        # Get the last message
        last_msg_stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.created_at))
            .limit(1)
        )

        msg_result = await db.execute(last_msg_stmt)
        last_message = msg_result.scalar_one_or_none()

        return {
            "id": str(conversation.id),
            "title": conversation.title,
            "created_at": (
                conversation.created_at.isoformat() if conversation.created_at else None
            ),
            "last_message_at": (
                conversation.last_message_at.isoformat()
                if conversation.last_message_at
                else None
            ),
            "last_message_preview": (
                last_message.content[:100] if last_message else None
            ),
            "message_count": (
                len(conversation.messages) if hasattr(conversation, "messages") else 0
            ),
        }
