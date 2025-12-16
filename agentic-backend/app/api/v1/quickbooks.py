"""
QuickBooks OAuth endpoints
Handles QuickBooks OAuth2 integration flow
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.utils.db import get_db
from app.core.security import get_current_tenant
from app.models.tenant import Tenant
from app.schema.quickbooks import (
    QuickBooksAuthURL,
    QuickBooksConnectionStatus,
    QuickBooksCompanyInfo,
    QuickBooksDisconnectResponse,
)
from app.services.quickbooks_service import QuickBooksService
from app.core.config import settings

router = APIRouter(prefix="/quickbooks", tags=["QuickBooks Integration"])


@router.get("/auth-url", response_model=QuickBooksAuthURL)
async def get_quickbooks_auth_url(
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Get QuickBooks OAuth authorization URL.

    Returns the URL to redirect user to for QuickBooks authorization.
    """
    auth_url = QuickBooksService.get_authorization_url(
        state=f"tenant_{current_tenant.id}"
    )
    return QuickBooksAuthURL(auth_url=auth_url)


@router.get("/callback")
async def quickbooks_callback(
    code: str,
    realmId: str,
    state: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    QuickBooks OAuth callback endpoint.

    QuickBooks redirects here after user authorizes the application.
    This endpoint exchanges the authorization code for tokens and saves the connection.
    """
    try:
        # Extract tenant_id from state if present
        tenant_id = None
        if state and state.startswith("tenant_"):
            tenant_id = state.replace("tenant_", "")

        # Exchange code for tokens
        tokens = await QuickBooksService.exchange_code_for_tokens(code, realmId)

        if not tenant_id:
            # If no tenant_id in state, return error or redirect to error page
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter",
            )

        # Get tenant
        from app.models.tenant import Tenant

        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant not found",
            )

        # Save connection for the tenant
        await QuickBooksService.save_connection(
            tenant_id=tenant_id,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=tokens["expires_in"],
            realm_id=realmId,
            db=db,
        )

        # Redirect to frontend success page
        frontend_url = settings.frontend_url
        return RedirectResponse(url=f"{frontend_url}/chat/accounts?connected=success")

    except HTTPException:
        raise
    except Exception as e:
        # Redirect to frontend error page
        frontend_url = settings.frontend_url
        return RedirectResponse(
            url=f"{frontend_url}/chat/accounts?connected=error&message={str(e)}"
        )


@router.get("/status", response_model=QuickBooksConnectionStatus)
async def get_connection_status(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get QuickBooks connection status for current tenant.

    Returns whether tenant is connected to QuickBooks and basic company information.

    This endpoint also checks token expiry and marks connection as inactive if needed.
    """
    # IMPORTANT: Check credentials first - this triggers token expiry check!
    from app.services.quickbooks_auth_service import get_quickbooks_credentials

    credentials = await get_quickbooks_credentials(current_tenant.id, db)

    # Now get the connection (might be inactive after credential check)
    connection = await QuickBooksService.get_tenant_connection(
        str(current_tenant.id), db
    )

    if not connection:
        # Never connected OR was marked inactive by get_quickbooks_credentials
        return QuickBooksConnectionStatus(
            is_connected=False, connection_expired=bool(not credentials)
        )

    if not connection.is_active:
        # Connection exists but expired (refresh token invalid)
        return QuickBooksConnectionStatus(
            is_connected=False,
            connection_expired=True,  # Let frontend know to show "reconnect" message
            company_name=connection.company_name,
            connected_at=connection.created_at,
        )

    # Active connection
    return QuickBooksConnectionStatus(
        is_connected=True,
        connection_expired=False,
        company_name=connection.company_name,
        company_country=connection.company_country,
        company_currency=connection.company_currency,
        realm_id=connection.realm_id,
        last_synced_at=connection.last_synced_at,
        connected_at=connection.created_at,
    )


@router.get("/company-info", response_model=QuickBooksCompanyInfo)
async def get_company_info(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed QuickBooks company information for tenant.

    Requires active QuickBooks connection.
    """
    connection = await QuickBooksService.get_tenant_connection(
        str(current_tenant.id), db
    )

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QuickBooks not connected",
        )

    if not connection.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="QuickBooks connection expired. Please reconnect your account.",
        )

    # Ensure token is valid
    access_token = await QuickBooksService.ensure_valid_token(connection, db)

    # Get company info from QuickBooks API
    try:
        company_data = await QuickBooksService.get_company_info(
            access_token=access_token,
            realm_id=connection.realm_id,
            use_sandbox=settings.quickbooks_use_sandbox,
        )

        company_info = company_data.get("CompanyInfo", {})

        return QuickBooksCompanyInfo(
            company_name=company_info.get("CompanyName", ""),
            legal_name=company_info.get("LegalName"),
            company_addr=company_info.get("CompanyAddr"),
            country=company_info.get("Country"),
            email=(
                company_info.get("Email", {}).get("Address")
                if company_info.get("Email")
                else None
            ),
            phone=(
                company_info.get("PrimaryPhone", {}).get("FreeFormNumber")
                if company_info.get("PrimaryPhone")
                else None
            ),
            fiscal_year_start_month=company_info.get("FiscalYearStartMonth"),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get company info: {str(e)}",
        )


@router.post("/disconnect", response_model=QuickBooksDisconnectResponse)
async def disconnect_quickbooks(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Disconnect QuickBooks integration for tenant.

    Revokes tokens and marks connection as inactive.
    """
    success = await QuickBooksService.disconnect(str(current_tenant.id), db)

    if success:
        return QuickBooksDisconnectResponse(
            success=True,
            message="Successfully disconnected from QuickBooks",
        )
    else:
        return QuickBooksDisconnectResponse(
            success=False,
            message="No active QuickBooks connection found",
        )
