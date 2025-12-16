"""
QuickBooks OAuth connection model
Stores QuickBooks access tokens and company information
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import UUID
from sqlmodel import Field, Relationship
from app.models.base import UUIDModel

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class QuickBooksConnection(UUIDModel, table=True):
    """QuickBooks OAuth connection for storing user's QB credentials"""

    __tablename__ = "quickbooks_connections"

    # Multi-tenancy - tenant owns the connection
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False, index=True)

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="quickbooks_connection")

    # OAuth tokens
    access_token: str = Field(nullable=False)
    refresh_token: str = Field(nullable=False)
    token_expires_at: datetime = Field(nullable=False)

    # QuickBooks company information
    realm_id: str = Field(nullable=False, index=True)  # QuickBooks Company ID
    company_name: Optional[str] = Field(default=None)
    company_country: Optional[str] = Field(default=None)
    company_currency: Optional[str] = Field(default=None)

    # Connection status
    is_active: bool = Field(default=True)
    last_synced_at: Optional[datetime] = Field(default=None)

    # Scopes granted
    scopes: Optional[str] = Field(default=None)  # Space-separated scopes
