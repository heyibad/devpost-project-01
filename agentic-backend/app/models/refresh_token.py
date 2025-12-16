from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID
from sqlmodel import Field, Relationship, SQLModel


if TYPE_CHECKING:
    from app.models.tenant import Tenant


class RefreshToken(SQLModel, table=True):
    """Refresh token model for JWT token management."""

    __tablename__ = "refresh_tokens"

    id: UUID = Field(
        default_factory=lambda: __import__("uuid").uuid4(),
        primary_key=True,
        nullable=False,
    )
    # Multi-tenancy
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False, index=True)

    token_hash: str = Field(nullable=False)
    expires_at: datetime = Field(nullable=False)
    revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="refresh_tokens")
