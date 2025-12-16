from typing import Optional, Any, TYPE_CHECKING
from uuid import UUID
from sqlmodel import Field, Relationship
from sqlalchemy import Index, Column, JSON
from app.models.base import UUIDModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.tenant import Tenant


class UserMessage(UUIDModel, table=True):
    """User Message model for conversation messages (phone-based users under tenant)."""

    __tablename__ = "user_messages"
    __table_args__ = (
        Index("ix_user_messages_phone", "phone_no"),
        Index("ix_user_messages_tenant", "tenant_id"),
        Index("ix_user_messages_created", "created_at"),
        # Composite index for fast queries by (tenant_id, phone_no)
        Index("ix_user_messages_tenant_phone", "tenant_id", "phone_no"),
    )

    # Multi-tenancy
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False, index=True)

    # Phone number for denormalized querying (no foreign key to avoid complexity)
    # This allows fast queries without joins: WHERE tenant_id = X AND phone_no = Y
    phone_no: Optional[str] = Field(default=None, nullable=True, index=True)
    
    role: str = Field(nullable=False)  # 'user'|'assistant'|'system'
    content: Optional[str] = Field(default=None, nullable=True)

    # Relationships
    tenant: Optional["Tenant"] = Relationship()
    # Remove user relationship since we're querying by phone_no directly
