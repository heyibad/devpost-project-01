"""
API endpoints for poster generation management
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import get_current_tenant
from app.models.tenant import Tenant
from app.schema.poster import PosterGenerationResponse, PosterListResponse
from app.services.poster_service import PosterService
from app.utils.db import get_db

router = APIRouter(prefix="/posters", tags=["posters"])


@router.get("", response_model=PosterListResponse)
async def get_posters(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Get all poster generations for the authenticated tenant

    Returns paginated list of posters with:
    - Image URL from ImageKit CDN
    - Caption text
    - Creation date
    - Poster ID

    Query parameters:
    - page: Page number (default: 1)
    - page_size: Number of items per page (default: 20, max: 100)
    """
    posters, total = await PosterService.get_posters_by_tenant(
        db=db,
        tenant_id=current_tenant.id,
        page=page,
        page_size=page_size,
    )

    # Convert to response schema
    poster_responses = [
        PosterGenerationResponse.model_validate(poster) for poster in posters
    ]

    return PosterListResponse.from_items(
        items=poster_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{poster_id}", response_model=PosterGenerationResponse)
async def get_poster(
    poster_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Get a specific poster generation by ID

    Returns:
    - Poster details if found and belongs to the authenticated tenant

    Raises:
    - 404: Poster not found or doesn't belong to tenant
    """
    poster = await PosterService.get_poster_by_id(
        db=db,
        poster_id=poster_id,
        tenant_id=current_tenant.id,
    )

    if not poster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Poster not found",
        )

    return PosterGenerationResponse.model_validate(poster)
