from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.utils.db import get_db
from app.schema.auth import (
    TenantRegister,
    TenantLogin,
    TokenResponse,
    TokenRefresh,
    AddPassword,
    ChangePassword,
    PasswordStatus,
)
from app.schema.user import TenantResponse
from app.services.auth_service import AuthService
from app.core.security import get_current_tenant
from app.models.tenant import Tenant
from app.models.app_settings import AppSettings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=TenantResponse, status_code=status.HTTP_201_CREATED
)
async def register(tenant_data: TenantRegister, db: AsyncSession = Depends(get_db)):
    """
    Register a new tenant.

    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **name**: Optional display name

    Returns the created tenant and authentication tokens.
    """
    tenant, tokens = await AuthService.register_tenant(tenant_data, db)

    # Convert tenant to dict to avoid lazy loading issues
    return TenantResponse(
        id=tenant.id,
        email=tenant.email,
        name=tenant.name,
        is_email_verified=tenant.is_email_verified,
        avatar_url=tenant.avatar_url,
        slug=tenant.slug,
        role=tenant.role,
        is_active=tenant.is_active,
        subscription_plan=tenant.subscription_plan,
        oauth_provider=tenant.oauth_provider,
        is_oauth_user=tenant.is_oauth_user,
        created_at=tenant.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(login_data: TenantLogin, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password.

    Returns access token (short-lived) and refresh token (long-lived).
    """
    tenant, tokens = await AuthService.login_tenant(login_data, db)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """
    Refresh access token using refresh token.

    The old refresh token will be revoked and a new one issued.
    """
    new_tokens = await AuthService.refresh_access_token(token_data.refresh_token, db)
    return new_tokens


@router.post("/logout")
async def logout(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Logout tenant by revoking refresh token.

    Requires a valid access token in Authorization header.
    """
    result = await AuthService.logout_tenant(token_data.refresh_token, db)
    return result


@router.get("/me", response_model=TenantResponse)
async def get_current_tenant_info(current_tenant: Tenant = Depends(get_current_tenant)):
    """
    Get current authenticated tenant's information.

    Requires valid access token in Authorization header.

    OPTIMIZATION: Uses cached tenant from get_current_tenant dependency (~0.1ms).
    The cache now stores primitive data and reconstructs Tenant objects,
    avoiding DetachedInstanceError issues.
    """
    return TenantResponse(
        id=current_tenant.id,
        email=current_tenant.email,
        name=current_tenant.name,
        is_email_verified=current_tenant.is_email_verified,
        avatar_url=current_tenant.avatar_url,
        slug=current_tenant.slug,
        role=current_tenant.role,
        is_active=current_tenant.is_active,
        subscription_plan=current_tenant.subscription_plan,
        oauth_provider=current_tenant.oauth_provider,
        is_oauth_user=current_tenant.is_oauth_user,
        created_at=current_tenant.created_at,
    )


@router.get("/verify-token")
async def verify_token(current_tenant: Tenant = Depends(get_current_tenant)):
    """
    Verify if the provided token is valid.

    Returns tenant ID if valid, otherwise 401 error.
    """
    return {
        "valid": True,
        "tenant_id": str(current_tenant.id),
        "email": current_tenant.email,
        "user_id": str(current_tenant.id),
    }


@router.get("/password-status", response_model=PasswordStatus)
async def get_password_status(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get password status for current tenant.

    Returns whether user has a password set and OAuth info.
    """
    result = await AuthService.get_password_status(current_tenant, db)
    return PasswordStatus(**result)


@router.post("/add-password")
async def add_password(
    password_data: AddPassword,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Add password for OAuth users who don't have one.

    This allows OAuth users to also login with email/password.
    """
    result = await AuthService.add_password(
        current_tenant,
        password_data.new_password,
        password_data.confirm_password,
        db,
    )
    return result


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Change password for users who already have one.

    Requires current password for verification.
    """
    result = await AuthService.change_password(
        current_tenant,
        password_data.old_password,
        password_data.new_password,
        db,
    )
    return result


@router.get("/waitlist-status")
async def get_waitlist_status(db: AsyncSession = Depends(get_db)):
    """
    Check if waitlist is enabled globally.

    This is a public endpoint that doesn't require authentication.
    Returns whether users need to go through waitlist approval.
    """
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    settings = result.scalar_one_or_none()

    if not settings:
        # Default: waitlist is enabled
        return {"waitlist_enabled": True}

    return {"waitlist_enabled": settings.waitlist_enabled}
