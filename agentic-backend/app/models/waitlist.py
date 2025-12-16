"""
Waitlist model for managing early access users.
Users are added to waitlist on signup and need manual approval to access the app.
"""

from typing import Optional, TYPE_CHECKING
from uuid import UUID
from datetime import datetime
from sqlmodel import Field, Relationship
from app.models.base import UUIDModel

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class Waitlist(UUIDModel, table=True):
    """
    Waitlist model for managing early access.
    Each tenant has one waitlist entry with their request message and approval status.
    """

    __tablename__ = "waitlist"

    # Foreign key to tenant
    tenant_id: UUID = Field(
        foreign_key="tenants.id", unique=True, index=True, nullable=False
    )

    # User's waitlist request message
    message: Optional[str] = Field(default=None, nullable=True, max_length=1000)

    # What features/use case they're interested in
    use_case: Optional[str] = Field(default=None, nullable=True, max_length=500)

    # Business name/type (optional extra info)
    business_type: Optional[str] = Field(default=None, nullable=True, max_length=200)

    # Approval status
    is_approved: bool = Field(default=False, index=True)
    approved_at: Optional[datetime] = Field(default=None, nullable=True)
    approved_by: Optional[str] = Field(
        default=None, nullable=True
    )  # Admin email who approved

    # Priority/notes for admin
    priority: int = Field(default=0)  # Higher = more priority
    admin_notes: Optional[str] = Field(default=None, nullable=True, max_length=500)

    # Relationship
    tenant: "Tenant" = Relationship(back_populates="waitlist_entry")
