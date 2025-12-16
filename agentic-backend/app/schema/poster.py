"""
Pydantic schemas for poster generation API responses
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PosterGenerationResponse(BaseModel):
    """Response schema for a single poster generation"""

    id: UUID
    tenant_id: UUID
    image_url: str
    image_caption: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PosterListResponse(BaseModel):
    """Paginated response schema for poster generations list"""

    items: list[PosterGenerationResponse]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_pages: int

    @classmethod
    def from_items(
        cls,
        items: list[PosterGenerationResponse],
        total: int,
        page: int,
        page_size: int,
    ) -> "PosterListResponse":
        """Create a paginated response from items and metadata"""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
