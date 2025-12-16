"""
Tenant/Organization model for multi-tenancy
Represents a company or organization in the system
"""

from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import UUIDModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.conversation import Conversation
    from app.models.quickbooks_connection import QuickBooksConnection
    from app.models.google_sheets_connection import GoogleSheetsConnection
    from app.models.whatsapp_cred import WhatsAppCred
    from app.models.message import Message
    from app.models.refresh_token import RefreshToken
    from app.models.poster_generation import PosterGeneration
    from app.models.waitlist import Waitlist


class Tenant(UUIDModel, table=True):
    """
    Tenant/Organization model for multi-tenancy.
    Represents a company or organization that uses the system.
    """

    __tablename__ = "tenants"

    # Basic information
    email: str = Field(unique=True, index=True, nullable=False)
    is_email_verified: bool = Field(default=False)
    password_hash: Optional[str] = Field(
        default=None, nullable=True
    )  # null for OAuth-only users
    name: Optional[str] = Field(default=None, nullable=True)
    avatar_url: Optional[str] = Field(default=None, nullable=True)

    # User role within the tenant
    role: str = Field(default="member", nullable=False)  # owner/admin/member/guest

    # OAuth fields
    oauth_provider: Optional[str] = Field(
        default=None, nullable=True
    )  # 'google', 'github', etc.
    oauth_id: Optional[str] = Field(
        default=None, nullable=True, index=True
    )  # Provider's user ID
    is_oauth_user: bool = Field(default=False)  # True if user registered via OAuth

    slug: str = Field(
        default=None, nullable=False, index=True
    )  # URL-friendly identifier

    # Contact information
    phone: Optional[str] = Field(default=None, nullable=True)
    website: Optional[str] = Field(default=None, nullable=True)

    # Address
    address: Optional[str] = Field(default=None, nullable=True)
    city: Optional[str] = Field(default=None, nullable=True)
    country: Optional[str] = Field(default=None, nullable=True)

    # Status and configuration
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)  # Admin users can access admin dashboard
    is_waitlist_approved: bool = Field(default=False)  # Waitlist approval status
    subscription_plan: Optional[str] = Field(
        default="free", nullable=True
    )  # free/basic/premium/enterprise
    max_users: int = Field(
        default=5, nullable=False
    )  # Maximum users allowed in this tenant

    # Settings (JSON field for flexible configuration)
    # settings: Optional[str] = Field(default=None, nullable=True)  # JSON string

    # Relationships
    refresh_tokens: list["RefreshToken"] = Relationship(
        back_populates="tenant",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    conversations: list["Conversation"] = Relationship(
        back_populates="tenant",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    messages: list["Message"] = Relationship(back_populates="tenant")
    users: list["User"] = Relationship(
        back_populates="tenant",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    quickbooks_connection: Optional["QuickBooksConnection"] = Relationship(
        back_populates="tenant",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
    google_sheets_connection: Optional["GoogleSheetsConnection"] = Relationship(
        back_populates="tenant",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
    whatsapp_creds: Optional["WhatsAppCred"] = Relationship(
        back_populates="tenant",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
    poster_generations: list["PosterGeneration"] = Relationship(
        back_populates="tenant",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    waitlist_entry: Optional["Waitlist"] = Relationship(
        back_populates="tenant",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"},
    )
