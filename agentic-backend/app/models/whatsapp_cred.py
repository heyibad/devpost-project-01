"""
Whatsapp credentials model for multi-tenant Evolution API connections.
"""

from typing import Optional, TYPE_CHECKING
from uuid import UUID
from sqlmodel import Field, Relationship
from app.models.base import UUIDModel

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class WhatsAppCred(UUIDModel, table=True):
    """WhatsApp credentials model for storing tenant's WhatsApp API credentials"""

    __tablename__ = "whatsapp_creds"

    # Multi-tenancy - tenant owns the connection
    instance_name: UUID = Field(
        foreign_key="tenants.id", nullable=False, index=True, unique=True
    )
    qr_code: Optional[str] = Field(default=None, nullable=True)

    # Connection status
    is_active: Optional[bool] = Field(default=True)

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="whatsapp_creds")