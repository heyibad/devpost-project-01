"""
Waitlist API endpoints for managing early access users.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.security import get_current_tenant
from app.models.tenant import Tenant
from app.models.waitlist import Waitlist
from app.utils.db import get_db


router = APIRouter(prefix="/waitlist", tags=["Waitlist"])


# ============================================================================
# Schemas
# ============================================================================


class WaitlistSubmitRequest(BaseModel):
    """Request to submit/update waitlist entry."""

    message: Optional[str] = Field(
        None, max_length=1000, description="Your message or request"
    )
    use_case: Optional[str] = Field(
        None, max_length=500, description="What you want to use Sahulat AI for"
    )
    business_type: Optional[str] = Field(
        None, max_length=200, description="Type of your business"
    )


class WaitlistStatusResponse(BaseModel):
    """Response with waitlist status."""

    is_on_waitlist: bool
    is_approved: bool
    position: Optional[int] = None  # Approximate position in queue
    message: Optional[str] = None
    use_case: Optional[str] = None
    business_type: Optional[str] = None
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None


class WaitlistSubmitResponse(BaseModel):
    """Response after submitting waitlist entry."""

    success: bool
    message: str
    waitlist_status: WaitlistStatusResponse


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/status", response_model=WaitlistStatusResponse)
async def get_waitlist_status(
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Get current user's waitlist status.
    Returns whether they're on the waitlist, approved, and their position.
    """
    # Check if user has a waitlist entry
    stmt = select(Waitlist).where(Waitlist.tenant_id == current_tenant.id)
    result = await db.execute(stmt)
    waitlist_entry = result.scalar_one_or_none()

    if not waitlist_entry:
        # No waitlist entry yet - they need to submit one
        return WaitlistStatusResponse(
            is_on_waitlist=False,
            is_approved=False,
            position=None,
            message=None,
            use_case=None,
            business_type=None,
            submitted_at=None,
            approved_at=None,
        )

    # Calculate approximate position (count of unapproved entries created before this one)
    position = None
    if not waitlist_entry.is_approved:
        count_stmt = select(Waitlist).where(
            Waitlist.is_approved == False,
            Waitlist.created_at < waitlist_entry.created_at,
        )
        count_result = await db.execute(count_stmt)
        position = len(count_result.all()) + 1

    return WaitlistStatusResponse(
        is_on_waitlist=True,
        is_approved=waitlist_entry.is_approved,
        position=position,
        message=waitlist_entry.message,
        use_case=waitlist_entry.use_case,
        business_type=waitlist_entry.business_type,
        submitted_at=waitlist_entry.created_at,
        approved_at=waitlist_entry.approved_at,
    )


@router.post("/submit", response_model=WaitlistSubmitResponse)
async def submit_waitlist(
    request: WaitlistSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Submit or update waitlist entry.
    Users can update their message/use_case while waiting.
    """
    # Check if user already has a waitlist entry
    stmt = select(Waitlist).where(Waitlist.tenant_id == current_tenant.id)
    result = await db.execute(stmt)
    waitlist_entry = result.scalar_one_or_none()

    if waitlist_entry:
        # Update existing entry (unless already approved)
        if waitlist_entry.is_approved:
            return WaitlistSubmitResponse(
                success=True,
                message="You're already approved! You can access all features.",
                waitlist_status=WaitlistStatusResponse(
                    is_on_waitlist=True,
                    is_approved=True,
                    position=None,
                    message=waitlist_entry.message,
                    use_case=waitlist_entry.use_case,
                    business_type=waitlist_entry.business_type,
                    submitted_at=waitlist_entry.created_at,
                    approved_at=waitlist_entry.approved_at,
                ),
            )

        # Update the entry
        if request.message is not None:
            waitlist_entry.message = request.message
        if request.use_case is not None:
            waitlist_entry.use_case = request.use_case
        if request.business_type is not None:
            waitlist_entry.business_type = request.business_type

        await db.commit()
        await db.refresh(waitlist_entry)

        # Calculate position
        count_stmt = select(Waitlist).where(
            Waitlist.is_approved == False,
            Waitlist.created_at < waitlist_entry.created_at,
        )
        count_result = await db.execute(count_stmt)
        position = len(count_result.all()) + 1

        return WaitlistSubmitResponse(
            success=True,
            message="Your waitlist entry has been updated!",
            waitlist_status=WaitlistStatusResponse(
                is_on_waitlist=True,
                is_approved=False,
                position=position,
                message=waitlist_entry.message,
                use_case=waitlist_entry.use_case,
                business_type=waitlist_entry.business_type,
                submitted_at=waitlist_entry.created_at,
                approved_at=None,
            ),
        )

    # Create new waitlist entry
    waitlist_entry = Waitlist(
        tenant_id=current_tenant.id,
        message=request.message,
        use_case=request.use_case,
        business_type=request.business_type,
    )
    db.add(waitlist_entry)
    await db.commit()
    await db.refresh(waitlist_entry)

    # Calculate position (last in queue)
    count_stmt = select(Waitlist).where(Waitlist.is_approved == False)
    count_result = await db.execute(count_stmt)
    position = len(count_result.all())

    return WaitlistSubmitResponse(
        success=True,
        message="You've been added to the waitlist! We'll notify you when you're approved.",
        waitlist_status=WaitlistStatusResponse(
            is_on_waitlist=True,
            is_approved=False,
            position=position,
            message=waitlist_entry.message,
            use_case=waitlist_entry.use_case,
            business_type=waitlist_entry.business_type,
            submitted_at=waitlist_entry.created_at,
            approved_at=None,
        ),
    )


@router.get("/check-access")
async def check_access(
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Quick endpoint to check if user has access to the app.
    Used by frontend to determine if user should be redirected to waitlist.
    """
    # Check tenant flag first (covers cases where admin toggled approval directly)
    tenant = await db.get(Tenant, current_tenant.id)
    tenant_flag = getattr(tenant, "is_waitlist_approved", False) if tenant else False

    # Check if user has an approved waitlist entry
    stmt = select(Waitlist).where(
        Waitlist.tenant_id == current_tenant.id, Waitlist.is_approved == True
    )
    result = await db.execute(stmt)
    approved_entry = result.scalar_one_or_none()

    has_access = tenant_flag or (approved_entry is not None)

    return {
        "has_access": has_access,
        "is_approved": has_access,
    }
