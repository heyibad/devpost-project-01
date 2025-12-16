"""
Tenant context utilities for multi-tenancy support
Provides tenant-aware database query filtering and utilities
"""

from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status, Depends, Request
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.tenant import Tenant
from app.models.user import User

async def get_tenant_id(request: Request) -> str:
    """
    Get tenant ID from the authenticated user's context.
    This is a FastAPI dependency that should be used in routes that require tenant context.
    
    Args:
        request: FastAPI request object with user info in state
        
    Returns:
        str: Tenant ID
        
    Raises:
        HTTPException: If no tenant ID is found or user is not authenticated
    """
    if not hasattr(request.state, "user") or not request.state.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    tenant_id = getattr(request.state.user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant ID found"
        )
    
    return str(tenant_id)


class TenantContext:
    """Utility class for tenant-aware operations"""

    @staticmethod
    async def get_tenant_by_id(tenant_id: UUID, db: AsyncSession) -> Optional[Tenant]:
        """
        Get tenant by ID.

        Args:
            tenant_id: Tenant UUID
            db: Database session

        Returns:
            Tenant object or None
        """
        statement = select(Tenant).where(Tenant.id == tenant_id)
        result = await db.exec(statement)
        return result.first()

    @staticmethod
    async def get_tenant_by_slug(slug: str, db: AsyncSession) -> Optional[Tenant]:
        """
        Get tenant by slug.

        Args:
            slug: Tenant slug (URL-friendly identifier)
            db: Database session

        Returns:
            Tenant object or None
        """
        statement = select(Tenant).where(Tenant.slug == slug)
        result = await db.exec(statement)
        return result.first()

    @staticmethod
    async def create_tenant(name: str, slug: str, db: AsyncSession, **kwargs) -> Tenant:
        """
        Create a new tenant.

        Args:
            name: Tenant name
            slug: URL-friendly identifier
            db: Database session
            **kwargs: Additional tenant fields

        Returns:
            Created Tenant object
        """
        # Check if slug already exists
        existing = await TenantContext.get_tenant_by_slug(slug, db)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tenant with slug '{slug}' already exists",
            )

        tenant = Tenant(name=name, slug=slug, **kwargs)
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        return tenant

    @staticmethod
    async def verify_user_tenant_access(
        user: User, tenant_id: UUID, db: AsyncSession, require_admin: bool = False
    ) -> bool:
        """
        Verify that a user has access to a tenant.

        Args:
            user: User object
            tenant_id: Tenant UUID to check
            db: Database session
            require_admin: If True, user must be admin or owner

        Returns:
            True if user has access, raises HTTPException otherwise
        """
        if str(user.tenant_id) != str(tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't belong to this organization",
            )

        if require_admin and user.role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Admin privileges required",
            )

        return True

    @staticmethod
    def get_tenant_filter(tenant_id: UUID):
        """
        Create a SQLAlchemy filter for tenant isolation.
        Use this in queries to automatically filter by tenant.

        Args:
            tenant_id: Tenant UUID

        Returns:
            Filter expression for tenant_id
        """
        return lambda model: model.tenant_id == tenant_id

    @staticmethod
    async def get_user_with_tenant(user_id: UUID, db: AsyncSession) -> Optional[User]:
        """
        Get user with their tenant information loaded.

        Args:
            user_id: User UUID
            db: Database session

        Returns:
            User object with tenant relationship loaded
        """
        from sqlmodel import select
        from app.models.user import User

        statement = select(User).where(User.id == user_id)
        result = await db.exec(statement)
        user = result.first()

        if user and user.tenant_id:
            # Load tenant relationship
            tenant_statement = select(Tenant).where(Tenant.id == user.tenant_id)
            tenant_result = await db.exec(tenant_statement)
            user.tenant = tenant_result.first()

        return user

    @staticmethod
    async def check_tenant_user_limit(tenant_id: UUID, db: AsyncSession) -> bool:
        """
        Check if tenant has reached maximum user limit.

        Args:
            tenant_id: Tenant UUID
            db: Database session

        Returns:
            True if under limit, False if limit reached
        """
        tenant = await TenantContext.get_tenant_by_id(tenant_id, db)
        if not tenant:
            return False

        # Count active users in tenant
        from app.models.user import User

        statement = select(User).where(User.tenant_id == tenant_id)
        result = await db.exec(statement)
        user_count = len(result.all())

        return user_count < tenant.max_users

    @staticmethod
    def ensure_tenant_id(user: User) -> UUID:
        """
        Ensure user has a tenant_id and return it.
        Raises exception if tenant_id is missing.

        Args:
            user: User object

        Returns:
            Tenant UUID
        """
        if not user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with any organization",
            )
        return user.tenant_id
