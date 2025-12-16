from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class TenantBase(BaseModel):
    """Base tenant schema"""

    email: EmailStr
    name: Optional[str] = None


class TenantResponse(TenantBase):
    """Tenant response schema"""

    id: UUID
    is_email_verified: bool
    avatar_url: Optional[str] = None
    slug: str
    role: str
    is_active: bool
    subscription_plan: Optional[str] = None
    oauth_provider: Optional[str] = None
    is_oauth_user: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TenantUpdate(BaseModel):
    """Tenant update schema"""

    name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


# Backward compatibility - keep User aliases
UserBase = TenantBase
UserResponse = TenantResponse
UserUpdate = TenantUpdate
