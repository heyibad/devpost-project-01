"""
User service with database operations using SQLModel.
Handles User sub-entity CRUD operations (phone-based users under a Tenant).

Note: Users in this context are sub-entities managed by Tenants.
They do NOT have authentication capabilities (no email/password/OAuth).
For authentication, see tenant_service.py and auth_service.py.
"""

from typing import Optional, List
from uuid import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user import User


async def get_user_by_phone(
    db: AsyncSession, phone_no: str, tenant_id: UUID
) -> Optional[User]:
    """Get user by phone number within a tenant."""
    statement = select(User).where(
        User.phone_no == phone_no,
        User.tenant_id == str(tenant_id),
    )
    result = await db.execute(statement)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Get user by UUID."""
    return await db.get(User, user_id)


async def get_users_by_tenant(
    db: AsyncSession, tenant_id: UUID, skip: int = 0, limit: int = 100
) -> List[User]:
    """Get all users belonging to a tenant."""
    statement = (
        select(User).where(User.tenant_id == str(tenant_id)).offset(skip).limit(limit)
    )
    result = await db.execute(statement)
    return list(result.scalars().all())


async def count_users_by_tenant(db: AsyncSession, tenant_id: UUID) -> int:
    """Count total users in a tenant."""
    from sqlalchemy import func

    statement = select(func.count(User.id)).where(User.tenant_id == str(tenant_id))
    result = await db.execute(statement)
    return result.scalar_one()


async def create_user(
    db: AsyncSession,
    tenant_id: UUID,
    phone_no: str,
    name: Optional[str] = None,
    role: Optional[str] = None,
) -> User:
    """
    Create a new user sub-entity under a tenant.

    Args:
        tenant_id: The parent tenant's ID
        phone_no: User's phone number (primary identifier)
        name: Optional display name
        role: Optional role (e.g., 'member', 'manager')
    """
    # Check if phone number already exists for this tenant
    existing = await get_user_by_phone(db, phone_no, tenant_id)
    if existing:
        raise ValueError(f"User with phone {phone_no} already exists in this tenant")

    user = User(
        tenant_id=str(tenant_id),
        phone_no=phone_no,
        name=name,
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user_id: UUID, **kwargs) -> Optional[User]:
    """
    Update user profile fields.

    Allowed fields: name, phone_no, role
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return None

    # Update allowed fields
    allowed_fields = {"name", "phone_no", "role"}
    for field, value in kwargs.items():
        if field in allowed_fields and value is not None:
            setattr(user, field, value)

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: UUID) -> bool:
    """
    Delete user sub-entity.
    This will cascade delete related user_conversations and user_messages.
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return False

    # Hard delete - cascade will handle related records
    await db.delete(user)
    await db.commit()
    return True


async def can_add_user_to_tenant(db: AsyncSession, tenant_id: UUID) -> bool:
    """
    Check if tenant can add more users based on their subscription plan.
    Returns True if under the limit, False otherwise.
    """
    from app.models.tenant import Tenant

    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        return False

    current_count = await count_users_by_tenant(db, tenant_id)
    max_users = tenant.max_users or 5  # Default to 5 if not set

    return current_count < max_users
