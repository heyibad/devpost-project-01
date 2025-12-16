"""
QuickBooks OAuth schemas for API requests and responses
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class QuickBooksAuthURL(BaseModel):
    """QuickBooks OAuth authorization URL response"""

    auth_url: str


class QuickBooksCallback(BaseModel):
    """QuickBooks OAuth callback data"""

    code: str
    realm_id: str  # QuickBooks Company ID
    state: Optional[str] = None


class QuickBooksConnectionStatus(BaseModel):
    """QuickBooks connection status response"""

    is_connected: bool
    connection_expired: bool = (
        False  # NEW: True if connection exists but is_active=False
    )
    company_name: Optional[str] = None
    company_country: Optional[str] = None
    company_currency: Optional[str] = None
    realm_id: Optional[str] = None
    last_synced_at: Optional[datetime] = None
    connected_at: Optional[datetime] = None


class QuickBooksCompanyInfo(BaseModel):
    """QuickBooks company information"""

    company_name: str
    legal_name: Optional[str] = None
    company_addr: Optional[dict] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fiscal_year_start_month: Optional[str] = None


class QuickBooksDisconnectResponse(BaseModel):
    """Response after disconnecting QuickBooks"""

    success: bool
    message: str
