from typing import Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from sqlmodel import Field, Relationship
from app.models.base import UUIDModel

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.tenant import Tenant


class Conversation(UUIDModel, table=True):
    """Conversation model for AI chat sessions."""

    __tablename__ = "conversations"

    # Multi-tenancy
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False, index=True)

    title: Optional[str] = Field(default=None, nullable=True)
    model: Optional[str] = Field(default=None, nullable=True)  # AI model used
    visibility: str = Field(default="private")  # private/shared
    last_message_at: Optional[datetime] = Field(
        default=None, nullable=True, index=True
    )  # For sorting conversations

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="conversations")
    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
