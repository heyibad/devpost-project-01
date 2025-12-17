"""
Admin API endpoints for managing users, waitlist, and viewing stats.
Only accessible by admin users (is_admin=True).
"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func, col

from app.core.security import get_current_admin
from app.models.tenant import Tenant
from app.models.waitlist import Waitlist
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.app_settings import AppSettings
from app.utils.db import get_db
from app.services.email_service import email_service


router = APIRouter(prefix="/admin", tags=["Admin"])


# ============================================================================
# Schemas
# ============================================================================


class DashboardStats(BaseModel):
    """Overall dashboard statistics."""

    total_users: int
    approved_users: int
    pending_waitlist: int
    total_conversations: int
    total_messages: int
    users_today: int
    users_this_week: int
    users_this_month: int


class WaitlistUserResponse(BaseModel):
    """Waitlist user with tenant details."""

    id: UUID
    tenant_id: UUID
    email: str
    name: Optional[str]
    is_approved: bool
    message: Optional[str]
    use_case: Optional[str]
    business_type: Optional[str]
    submitted_at: datetime
    approved_at: Optional[datetime]
    oauth_provider: Optional[str]
    avatar_url: Optional[str]


class WaitlistListResponse(BaseModel):
    """Paginated waitlist response."""

    items: List[WaitlistUserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserResponse(BaseModel):
    """User/tenant details for admin view."""

    id: UUID
    email: str
    name: Optional[str]
    is_active: bool
    is_admin: bool
    is_waitlist_approved: bool
    oauth_provider: Optional[str]
    avatar_url: Optional[str]
    subscription_plan: Optional[str]
    created_at: datetime
    conversation_count: int = 0
    message_count: int = 0


class UserListResponse(BaseModel):
    """Paginated user list response."""

    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ApproveUserRequest(BaseModel):
    """Request to approve/reject a user."""

    send_email: bool = Field(
        default=True, description="Whether to send notification email"
    )


class ApproveUserResponse(BaseModel):
    """Response after approving/rejecting user."""

    success: bool
    message: str
    email_sent: bool = False


class UpdateUserRequest(BaseModel):
    """Request to update user details."""

    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    subscription_plan: Optional[str] = None


class WaitlistSettingsResponse(BaseModel):
    """Response for waitlist settings."""

    waitlist_enabled: bool
    updated_at: datetime
    updated_by: Optional[str] = None


class WaitlistSettingsRequest(BaseModel):
    """Request to update waitlist settings."""

    waitlist_enabled: bool


class BulkApproveRequest(BaseModel):
    """Request to bulk approve/reject users."""

    user_ids: List[UUID]
    send_email: bool = True


class BulkApproveResponse(BaseModel):
    """Response after bulk approve/reject."""

    success_count: int
    failed_count: int
    message: str


class SendEmailRequest(BaseModel):
    """Request to send custom email to users."""

    to_emails: List[str]
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)


class SendEmailResponse(BaseModel):
    """Response after sending emails."""

    success_count: int
    failed: List[str]
    message: str


# ============================================================================
# Admin Check Endpoint
# ============================================================================


@router.get("/check")
async def check_admin_access(
    current_admin: Tenant = Depends(get_current_admin),
):
    """Check if current user has admin access."""
    return {
        "is_admin": True,
        "email": current_admin.email,
        "name": current_admin.name,
    }


# ============================================================================
# Waitlist Settings (Global Toggle)
# ============================================================================


@router.get("/settings/waitlist", response_model=WaitlistSettingsResponse)
async def get_waitlist_settings(
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
):
    """Get the global waitlist settings."""
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()

    if not settings:
        # Create default settings if not exists
        settings = AppSettings(id=1, waitlist_enabled=True)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return WaitlistSettingsResponse(
        waitlist_enabled=settings.waitlist_enabled,
        updated_at=settings.updated_at,
        updated_by=settings.updated_by,
    )


@router.put("/settings/waitlist", response_model=WaitlistSettingsResponse)
async def update_waitlist_settings(
    request: WaitlistSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
):
    """Enable or disable the global waitlist requirement."""
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()

    if not settings:
        settings = AppSettings(
            id=1,
            waitlist_enabled=request.waitlist_enabled,
            updated_by=current_admin.email,
        )
        db.add(settings)
    else:
        settings.waitlist_enabled = request.waitlist_enabled
        settings.updated_at = datetime.utcnow()
        settings.updated_by = current_admin.email

    await db.commit()
    await db.refresh(settings)

    return WaitlistSettingsResponse(
        waitlist_enabled=settings.waitlist_enabled,
        updated_at=settings.updated_at,
        updated_by=settings.updated_by,
    )


# ============================================================================
# Dashboard Stats
# ============================================================================


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
):
    """Get overall dashboard statistics."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)

    # Total users
    total_users_result = await db.execute(select(func.count(Tenant.id)))
    total_users = total_users_result.scalar() or 0

    # Approved users (waitlist approved)
    approved_stmt = select(func.count(Waitlist.id)).where(Waitlist.is_approved == True)
    approved_result = await db.execute(approved_stmt)
    approved_users = approved_result.scalar() or 0

    # Pending waitlist
    pending_stmt = select(func.count(Waitlist.id)).where(Waitlist.is_approved == False)
    pending_result = await db.execute(pending_stmt)
    pending_waitlist = pending_result.scalar() or 0

    # Total conversations
    conv_result = await db.execute(select(func.count(Conversation.id)))
    total_conversations = conv_result.scalar() or 0

    # Total messages
    msg_result = await db.execute(select(func.count(Message.id)))
    total_messages = msg_result.scalar() or 0

    # Users today
    today_stmt = select(func.count(Tenant.id)).where(Tenant.created_at >= today_start)
    today_result = await db.execute(today_stmt)
    users_today = today_result.scalar() or 0

    # Users this week
    week_stmt = select(func.count(Tenant.id)).where(Tenant.created_at >= week_start)
    week_result = await db.execute(week_stmt)
    users_this_week = week_result.scalar() or 0

    # Users this month
    month_stmt = select(func.count(Tenant.id)).where(Tenant.created_at >= month_start)
    month_result = await db.execute(month_stmt)
    users_this_month = month_result.scalar() or 0

    return DashboardStats(
        total_users=total_users,
        approved_users=approved_users,
        pending_waitlist=pending_waitlist,
        total_conversations=total_conversations,
        total_messages=total_messages,
        users_today=users_today,
        users_this_week=users_this_week,
        users_this_month=users_this_month,
    )


# ============================================================================
# Waitlist Management
# ============================================================================


@router.get("/waitlist", response_model=WaitlistListResponse)
async def get_waitlist(
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(
        None, description="Filter: 'pending', 'approved', or 'all'"
    ),
    search: Optional[str] = Query(None, description="Search by email or name"),
):
    """Get paginated waitlist with filters."""
    # Base query with join to get tenant info
    base_query = select(Waitlist, Tenant).join(Tenant, Waitlist.tenant_id == Tenant.id)

    # Apply status filter
    if status_filter == "pending":
        base_query = base_query.where(Waitlist.is_approved == False)
    elif status_filter == "approved":
        base_query = base_query.where(Waitlist.is_approved == True)

    # Apply search filter
    if search:
        search_term = f"%{search.lower()}%"
        base_query = base_query.where(
            (func.lower(Tenant.email).like(search_term))
            | (func.lower(Tenant.name).like(search_term))
        )

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination and ordering (newest first)
    offset = (page - 1) * page_size
    paginated_query = (
        base_query.order_by(Waitlist.created_at.desc()).offset(offset).limit(page_size)
    )

    result = await db.execute(paginated_query)
    rows = result.all()

    # Build response items
    items = []
    for waitlist, tenant in rows:
        items.append(
            WaitlistUserResponse(
                id=waitlist.id,
                tenant_id=tenant.id,
                email=tenant.email,
                name=tenant.name,
                is_approved=waitlist.is_approved,
                message=waitlist.message,
                use_case=waitlist.use_case,
                business_type=waitlist.business_type,
                submitted_at=waitlist.created_at,
                approved_at=waitlist.approved_at,
                oauth_provider=tenant.oauth_provider,
                avatar_url=tenant.avatar_url,
            )
        )

    total_pages = (total + page_size - 1) // page_size

    return WaitlistListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/waitlist/{waitlist_id}/approve", response_model=ApproveUserResponse)
async def approve_waitlist_user(
    waitlist_id: UUID,
    request: ApproveUserRequest = ApproveUserRequest(),
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
):
    """Approve a user from the waitlist."""
    # Get waitlist entry
    stmt = select(Waitlist).where(Waitlist.id == waitlist_id)
    result = await db.execute(stmt)
    waitlist_entry = result.scalar_one_or_none()

    if not waitlist_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Waitlist entry not found"
        )

    if waitlist_entry.is_approved:
        return ApproveUserResponse(
            success=True,
            message="User is already approved",
            email_sent=False,
        )

    # Get tenant for email
    tenant = await db.get(Tenant, waitlist_entry.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Store email and name BEFORE commit (to avoid lazy load after commit)
    tenant_email = tenant.email
    tenant_name = tenant.name

    # Approve the user
    waitlist_entry.is_approved = True
    waitlist_entry.approved_at = datetime.utcnow()
    tenant.is_waitlist_approved = True

    await db.commit()

    # Send email notification (using stored values)
    email_sent = False
    if request.send_email:
        email_sent = await email_service.send_waitlist_approval_email(
            to_email=tenant_email,
            user_name=tenant_name,
        )

    # Clear in-memory user cache so the user's subsequent requests reflect the
    # updated is_waitlist_approved flag immediately (get_current_tenant caches
    # primitive tenant data for a short TTL).
    try:
        # Import here to avoid circular imports at module load
        from app.core import security

        security._user_cache.pop(str(tenant.id), None)
    except Exception:
        # Non-fatal: if cache clearing fails, continue (cache will expire)
        pass

    return ApproveUserResponse(
        success=True,
        message=f"User {tenant_email} has been approved!",
        email_sent=email_sent,
    )


@router.post("/waitlist/{waitlist_id}/reject", response_model=ApproveUserResponse)
async def reject_waitlist_user(
    waitlist_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
):
    """Reject/unapprove a user from the waitlist."""
    # Get waitlist entry
    stmt = select(Waitlist).where(Waitlist.id == waitlist_id)
    result = await db.execute(stmt)
    waitlist_entry = result.scalar_one_or_none()

    if not waitlist_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Waitlist entry not found"
        )

    # Get tenant
    tenant = await db.get(Tenant, waitlist_entry.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Store email BEFORE commit
    tenant_email = tenant.email

    # Reject/unapprove the user
    waitlist_entry.is_approved = False
    waitlist_entry.approved_at = None
    tenant.is_waitlist_approved = False

    await db.commit()

    # Clear in-memory user cache so revocation is reflected quickly
    try:
        from app.core import security

        security._user_cache.pop(str(tenant.id), None)
    except Exception:
        pass

    return ApproveUserResponse(
        success=True,
        message=f"User {tenant_email} access has been revoked",
        email_sent=False,
    )


# ============================================================================
# User Management
# ============================================================================


@router.get("/users", response_model=UserListResponse)
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by email or name"),
    admin_only: bool = Query(False, description="Show only admin users"),
):
    """Get paginated list of all users."""
    # Base query
    base_query = select(Tenant)

    # Apply filters
    if admin_only:
        base_query = base_query.where(Tenant.is_admin == True)

    if search:
        search_term = f"%{search.lower()}%"
        base_query = base_query.where(
            (func.lower(Tenant.email).like(search_term))
            | (func.lower(Tenant.name).like(search_term))
        )

    # Get total count
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    paginated_query = (
        base_query.order_by(Tenant.created_at.desc()).offset(offset).limit(page_size)
    )

    result = await db.execute(paginated_query)
    tenants = result.scalars().all()

    # Build response with conversation/message counts
    items = []
    for tenant in tenants:
        # Get conversation count
        conv_stmt = select(func.count(Conversation.id)).where(
            Conversation.tenant_id == tenant.id
        )
        conv_result = await db.execute(conv_stmt)
        conv_count = conv_result.scalar() or 0

        # Get message count
        msg_stmt = select(func.count(Message.id)).where(Message.tenant_id == tenant.id)
        msg_result = await db.execute(msg_stmt)
        msg_count = msg_result.scalar() or 0

        items.append(
            UserResponse(
                id=tenant.id,
                email=tenant.email,
                name=tenant.name,
                is_active=tenant.is_active,
                is_admin=getattr(tenant, "is_admin", False),
                is_waitlist_approved=getattr(tenant, "is_waitlist_approved", False),
                oauth_provider=tenant.oauth_provider,
                avatar_url=tenant.avatar_url,
                subscription_plan=tenant.subscription_plan,
                created_at=tenant.created_at,
                conversation_count=conv_count,
                message_count=msg_count,
            )
        )

    total_pages = (total + page_size - 1) // page_size

    return UserListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    request: UpdateUserRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
):
    """Update user details (admin status, active status, subscription)."""
    tenant = await db.get(Tenant, user_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Update fields if provided
    if request.is_admin is not None:
        tenant.is_admin = request.is_admin
    if request.is_active is not None:
        tenant.is_active = request.is_active
    if request.subscription_plan is not None:
        tenant.subscription_plan = request.subscription_plan

    await db.commit()
    await db.refresh(tenant)

    # Get counts
    conv_stmt = select(func.count(Conversation.id)).where(
        Conversation.tenant_id == tenant.id
    )
    conv_result = await db.execute(conv_stmt)
    conv_count = conv_result.scalar() or 0

    msg_stmt = select(func.count(Message.id)).where(Message.tenant_id == tenant.id)
    msg_result = await db.execute(msg_stmt)
    msg_count = msg_result.scalar() or 0

    return UserResponse(
        id=tenant.id,
        email=tenant.email,
        name=tenant.name,
        is_active=tenant.is_active,
        is_admin=getattr(tenant, "is_admin", False),
        is_waitlist_approved=getattr(tenant, "is_waitlist_approved", False),
        oauth_provider=tenant.oauth_provider,
        avatar_url=tenant.avatar_url,
        subscription_plan=tenant.subscription_plan,
        created_at=tenant.created_at,
        conversation_count=conv_count,
        message_count=msg_count,
    )


@router.post("/users/{user_id}/make-admin", response_model=ApproveUserResponse)
async def make_user_admin(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
):
    """Grant admin privileges to a user."""
    tenant = await db.get(Tenant, user_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Store email BEFORE commit to avoid lazy load after session closed
    tenant_email = tenant.email

    tenant.is_admin = True
    await db.commit()

    # Clear user cache so the change is reflected immediately
    try:
        from app.core import security

        security._user_cache.pop(str(tenant.id), None)
    except Exception:
        pass

    return ApproveUserResponse(
        success=True,
        message=f"User {tenant_email} is now an admin",
        email_sent=False,
    )


@router.post("/users/{user_id}/remove-admin", response_model=ApproveUserResponse)
async def remove_user_admin(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
):
    """Remove admin privileges from a user."""
    tenant = await db.get(Tenant, user_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Prevent removing own admin access
    if tenant.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin privileges",
        )

    # Store email BEFORE commit to avoid lazy load after session closed
    tenant_email = tenant.email

    tenant.is_admin = False
    await db.commit()

    # Clear user cache so the change is reflected immediately
    try:
        from app.core import security

        security._user_cache.pop(str(tenant.id), None)
    except Exception:
        pass

    return ApproveUserResponse(
        success=True,
        message=f"Admin privileges removed from {tenant_email}",
        email_sent=False,
    )


@router.post("/users/{user_id}/toggle-access", response_model=ApproveUserResponse)
async def toggle_user_access(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
):
    """Toggle access for a user (approve/revoke). Works for any user."""
    tenant = await db.get(Tenant, user_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Prevent revoking own access
    if tenant.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke your own access",
        )

    # Store email BEFORE commit
    tenant_email = tenant.email
    
    # Toggle the access
    new_status = not tenant.is_waitlist_approved
    tenant.is_waitlist_approved = new_status
    
    # Also update waitlist entry if exists
    stmt = select(Waitlist).where(Waitlist.tenant_id == user_id)
    result = await db.execute(stmt)
    waitlist_entry = result.scalar_one_or_none()
    
    if waitlist_entry:
        waitlist_entry.is_approved = new_status
        if new_status:
            from datetime import datetime, timezone
            waitlist_entry.approved_at = datetime.now(timezone.utc)
            waitlist_entry.approved_by_admin_id = current_admin.id
        else:
            waitlist_entry.approved_at = None
    
    await db.commit()

    # Clear user cache so the change is reflected immediately
    try:
        from app.core import security
        security._user_cache.pop(str(tenant.id), None)
    except Exception:
        pass

    action = "approved" if new_status else "revoked"
    return ApproveUserResponse(
        success=True,
        message=f"Access {action} for {tenant_email}",
        email_sent=False,
    )


# ============================================================================
# Bulk Actions
# ============================================================================


@router.post("/waitlist/bulk-approve", response_model=BulkApproveResponse)
async def bulk_approve_users(
    request: BulkApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
):
    """Bulk approve multiple waitlist users."""
    success_count = 0
    failed_count = 0

    for user_id in request.user_ids:
        try:
            # Get waitlist entry
            stmt = select(Waitlist).where(Waitlist.id == user_id)
            result = await db.execute(stmt)
            waitlist = result.scalar_one_or_none()

            if not waitlist or waitlist.is_approved:
                failed_count += 1
                continue

            # Approve
            waitlist.is_approved = True
            waitlist.approved_at = datetime.utcnow()

            # Update tenant
            tenant = await db.get(Tenant, waitlist.tenant_id)
            if tenant:
                tenant.is_waitlist_approved = True

                # Send email if requested
                if request.send_email:
                    await email_service.send_waitlist_approval_email(
                        to_email=tenant.email,
                        user_name=tenant.name,
                    )

            success_count += 1

        except Exception as e:
            print(f"Error approving user {user_id}: {e}")
            failed_count += 1

    await db.commit()

    return BulkApproveResponse(
        success_count=success_count,
        failed_count=failed_count,
        message=f"Successfully approved {success_count} users, {failed_count} failed",
    )


@router.post("/waitlist/bulk-reject", response_model=BulkApproveResponse)
async def bulk_reject_users(
    request: BulkApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
):
    """Bulk reject/revoke multiple waitlist users."""
    success_count = 0
    failed_count = 0

    for user_id in request.user_ids:
        try:
            stmt = select(Waitlist).where(Waitlist.id == user_id)
            result = await db.execute(stmt)
            waitlist = result.scalar_one_or_none()

            if not waitlist:
                failed_count += 1
                continue

            # Revoke approval
            waitlist.is_approved = False
            waitlist.approved_at = None

            # Update tenant
            tenant = await db.get(Tenant, waitlist.tenant_id)
            if tenant:
                tenant.is_waitlist_approved = False

            success_count += 1

        except Exception as e:
            print(f"Error rejecting user {user_id}: {e}")
            failed_count += 1

    await db.commit()

    return BulkApproveResponse(
        success_count=success_count,
        failed_count=failed_count,
        message=f"Successfully rejected {success_count} users, {failed_count} failed",
    )


# ============================================================================
# Email Composer
# ============================================================================


@router.post("/send-email", response_model=SendEmailResponse)
async def send_custom_email(
    request: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
):
    """Send a custom email to one or more users."""
    result = await email_service.send_custom_email(
        to_emails=request.to_emails,
        subject=request.subject,
        message=request.message,
        sender_name=current_admin.name or "Sahulat AI Team",
    )

    return SendEmailResponse(
        success_count=result.get("success_count", 0),
        failed=result.get("failed", []),
        message=f"Successfully sent {result.get('success_count', 0)} emails",
    )


@router.get("/users/emails")
async def get_all_user_emails(
    approved_only: bool = Query(False, description="Only return approved users"),
    db: AsyncSession = Depends(get_db),
    current_admin: Tenant = Depends(get_current_admin),
):
    """Get all user emails for email composer autocomplete."""
    if approved_only:
        stmt = select(Tenant.email, Tenant.name).where(Tenant.is_waitlist_approved == True)
    else:
        stmt = select(Tenant.email, Tenant.name)

    result = await db.execute(stmt)
    users = result.all()

    return [
        {"email": email, "name": name or email.split("@")[0]}
        for email, name in users
    ]
