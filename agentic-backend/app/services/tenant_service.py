"""
Tenant service with database operations using SQLModel.
Handles tenant CRUD operations and profile management.
Note: Authentication is handled by AuthService and OAuthService.
"""

from typing import Optional
from uuid import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.tenant import Tenant
from app.core.security import hash_password, verify_password


async def get_tenant_by_email(db: AsyncSession, email: str) -> Optional[Tenant]:
    """Get tenant by email address."""
    statement = select(Tenant).where(Tenant.email == email)
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def get_tenant_by_slug(db: AsyncSession, slug: str) -> Optional[Tenant]:
    """Get tenant by slug."""
    statement = select(Tenant).where(Tenant.slug == slug)
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def get_tenant_by_id(db: AsyncSession, tenant_id: UUID) -> Optional[Tenant]:
    """Get tenant by UUID."""
    return await db.get(Tenant, tenant_id)


async def get_tenant_by_oauth(
    db: AsyncSession, oauth_provider: str, oauth_id: str
) -> Optional[Tenant]:
    """Get tenant by OAuth provider and ID."""
    statement = select(Tenant).where(
        Tenant.oauth_provider == oauth_provider,
        Tenant.oauth_id == oauth_id,
    )
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def update_tenant(
    db: AsyncSession, tenant_id: UUID, **kwargs
) -> Optional[Tenant]:
    """
    Update tenant profile fields.

    Allowed fields: name, phone, website, address fields, logo_url, primary_color, settings
    """
    tenant = await get_tenant_by_id(db, tenant_id)
    if not tenant:
        return None

    # Update allowed fields
    allowed_fields = {
        "name",
        "phone",
        "website",
        "address_line1",
        "address_line2",
        "city",
        "state",
        "postal_code",
        "country",
        "logo_url",
        "primary_color",
        "settings",
        "subscription_plan",
        "max_users",
    }

    for field, value in kwargs.items():
        if field in allowed_fields and value is not None:
            setattr(tenant, field, value)

    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


async def update_tenant_password(
    db: AsyncSession, tenant_id: UUID, new_password: str
) -> Optional[Tenant]:
    """Update tenant password with new hashed password."""
    tenant = await get_tenant_by_id(db, tenant_id)
    if not tenant:
        return None

    tenant.password_hash = hash_password(new_password)
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


async def verify_tenant_password(tenant: Tenant, password: str) -> bool:
    """Verify tenant password against stored hash."""
    if not tenant.password_hash:
        return False
    return verify_password(password, tenant.password_hash)


async def update_tenant_email(
    db: AsyncSession, tenant_id: UUID, new_email: str
) -> Optional[Tenant]:
    """
    Update tenant email address.
    Note: This will reset email verification status.
    """
    tenant = await get_tenant_by_id(db, tenant_id)
    if not tenant:
        return None

    # Check if email is already taken
    existing = await get_tenant_by_email(db, new_email)
    if existing and existing.id != tenant_id:
        raise ValueError("Email already in use")

    tenant.email = new_email
    tenant.is_email_verified = False
    tenant.email_verified_at = None

    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


async def verify_tenant_email(db: AsyncSession, tenant_id: UUID) -> Optional[Tenant]:
    """Mark tenant email as verified."""
    from datetime import datetime

    tenant = await get_tenant_by_id(db, tenant_id)
    if not tenant:
        return None

    tenant.is_email_verified = True
    tenant.email_verified_at = datetime.utcnow()

    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    return tenant


async def deactivate_tenant(db: AsyncSession, tenant_id: UUID) -> bool:
    """
    Deactivate tenant account (soft delete).
    Tenant can be reactivated later.
    """
    tenant = await get_tenant_by_id(db, tenant_id)
    if not tenant:
        return False

    tenant.is_active = False
    db.add(tenant)
    await db.commit()
    return True


async def activate_tenant(db: AsyncSession, tenant_id: UUID) -> bool:
    """Reactivate a deactivated tenant account."""
    tenant = await get_tenant_by_id(db, tenant_id)
    if not tenant:
        return False

    tenant.is_active = True
    db.add(tenant)
    await db.commit()
    return True


async def delete_tenant(db: AsyncSession, tenant_id: UUID) -> bool:
    """
    Delete tenant account permanently (hard delete).
    WARNING: This will cascade delete all related data (users, conversations, messages, etc.)
    """
    tenant = await get_tenant_by_id(db, tenant_id)
    if not tenant:
        return False

    # Hard delete - cascade will handle related records
    await db.delete(tenant)
    await db.commit()
    return True


async def update_last_login(db: AsyncSession, tenant_id: UUID) -> None:
    """Update tenant's last login timestamp."""
    from datetime import datetime

    tenant = await get_tenant_by_id(db, tenant_id)
    if tenant:
        tenant.last_login_at = datetime.utcnow()
        db.add(tenant)
        await db.commit()
