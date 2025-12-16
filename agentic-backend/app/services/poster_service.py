"""
Service layer for poster generation operations
"""

from typing import Optional
from uuid import UUID
from sqlalchemy import select, func, cast, String, desc
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.poster_generation import PosterGeneration


class PosterService:
    """Service for managing poster generations"""

    @staticmethod
    async def get_posters_by_tenant(
        db: AsyncSession,
        tenant_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PosterGeneration], int]:
        """
        Get all poster generations for a tenant with pagination

        Args:
            db: Database session
            tenant_id: Tenant UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (list of poster generations, total count)
        """
        # Calculate offset
        offset = (page - 1) * page_size

        # Convert UUID to string for comparison (handles VARCHAR column type)
        tenant_id_str = str(tenant_id)

        # Query for posters with pagination
        query = (
            select(PosterGeneration)
            .where(cast(PosterGeneration.tenant_id, String) == tenant_id_str)
            .order_by(desc(PosterGeneration.created_at))
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(query)
        posters = result.scalars().all()

        # Get total count
        count_query = select(func.count(PosterGeneration.id)).where(
            cast(PosterGeneration.tenant_id, String) == tenant_id_str
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        return list(posters), total

    @staticmethod
    async def get_poster_by_id(
        db: AsyncSession,
        poster_id: UUID,
        tenant_id: UUID,
    ) -> Optional[PosterGeneration]:
        """
        Get a specific poster generation by ID

        Args:
            db: Database session
            poster_id: Poster UUID
            tenant_id: Tenant UUID for authorization

        Returns:
            PosterGeneration if found and belongs to tenant, None otherwise
        """
        # Convert UUIDs to strings for comparison (handles VARCHAR column type)
        poster_id_str = str(poster_id)
        tenant_id_str = str(tenant_id)

        query = select(PosterGeneration).where(
            cast(PosterGeneration.id, String) == poster_id_str,
            cast(PosterGeneration.tenant_id, String) == tenant_id_str,
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
