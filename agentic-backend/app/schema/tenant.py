"""
Tenant/Organization schemas for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class TenantCreate(BaseModel):
    """Schema for creating a new tenant"""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    subscription_plan: Optional[str] = "free"


class TenantUpdate(BaseModel):
    """Schema for updating tenant information"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    is_active: Optional[bool] = None
    subscription_plan: Optional[str] = None
    max_users: Optional[int] = None


class TenantResponse(BaseModel):
    """Schema for tenant response"""

    id: UUID
    name: str
    slug: str
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_active: bool
    subscription_plan: Optional[str] = None
    max_users: int
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TenantStats(BaseModel):
    """Schema for tenant statistics"""

    user_count: int
    conversation_count: int
    message_count: int
    quickbooks_connected: bool
    is_at_user_limit: bool


class TenantWithStats(TenantResponse):
    """Tenant response with statistics"""

    stats: Optional[TenantStats] = None
