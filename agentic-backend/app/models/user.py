from typing import Optional, TYPE_CHECKING
from uuid import UUID
from sqlmodel import Field, Relationship
from sqlalchemy import UniqueConstraint
from app.models.base import UUIDModel

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class User(UUIDModel, table=True):
    """User sub-entity model - phone-based users managed by a Tenant."""

    __tablename__ = "users"
    __table_args__ = (
        # Composite unique constraint: one phone number per tenant
        UniqueConstraint("phone_no", "tenant_id", name="uq_user_phone_tenant"),
    )

    # Phone number (indexed for fast queries)
    phone_no: str = Field(nullable=False, index=True)

    # Multi-tenancy - belongs to a tenant
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False, index=True)

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="users")
