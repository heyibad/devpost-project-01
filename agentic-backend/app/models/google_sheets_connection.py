"""
Google Sheets OAuth connection model
Stores Google Sheets access tokens and sheet configuration
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import UUID
from sqlmodel import Field, Relationship
from app.models.base import UUIDModel

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class GoogleSheetsConnection(UUIDModel, table=True):
    """Google Sheets OAuth connection for storing tenant's Google Sheets credentials"""

    __tablename__ = "google_sheets_connections"

    # Multi-tenancy - tenant owns the connection
    tenant_id: UUID = Field(
        foreign_key="tenants.id", nullable=False, index=True, unique=True
    )

    # Relationships
    tenant: Optional["Tenant"] = Relationship(back_populates="google_sheets_connection")

    # OAuth tokens
    access_token: str = Field(nullable=False)
    refresh_token: str = Field(nullable=False)
    token_expires_at: datetime = Field(nullable=False)

    # Inventory sheet configuration
    inventory_workbook_id: Optional[str] = Field(default=None, nullable=True)
    inventory_worksheet_name: Optional[str] = Field(default=None, nullable=True)

    # Orders sheet configuration
    orders_workbook_id: Optional[str] = Field(default=None, nullable=True)
    orders_worksheet_name: Optional[str] = Field(default=None, nullable=True)

    # Connection status
    is_active: bool = Field(default=True)
    last_synced_at: Optional[datetime] = Field(default=None)

    # Scopes granted
    scopes: Optional[str] = Field(default=None)  # Space-separated scopes
