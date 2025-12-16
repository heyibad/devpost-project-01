"""
Google Sheets OAuth endpoints
Handles Google Sheets OAuth2 integration flow
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from uuid import UUID

from app.utils.db import get_db
from app.core.security import get_current_tenant
from app.models.tenant import Tenant
from app.schema.google_sheets import (
    GoogleSheetsAuthURL,
    GoogleSheetsConnectionStatus,
    SpreadsheetsListResponse,
    WorksheetsListResponse,
    SaveSheetsConfigRequest,
    GoogleSheetsDisconnectResponse,
    SpreadsheetInfo,
    WorksheetInfo,
    OrdersDataResponse,
    OrderItem,
    OrdersStats,
)
from app.services.google_sheets_service import GoogleSheetsService
from app.core.config import settings

router = APIRouter(prefix="/google-sheets", tags=["Google Sheets Integration"])


@router.get("/auth-url", response_model=GoogleSheetsAuthURL)
async def get_google_sheets_auth_url(
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Get Google Sheets OAuth authorization URL.

    Returns the URL to redirect user to for Google Sheets authorization.
    """
    auth_url = GoogleSheetsService.get_authorization_url(
        state=f"tenant_{current_tenant.id}"
    )
    return GoogleSheetsAuthURL(auth_url=auth_url)


@router.get("/callback")
async def google_sheets_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str | None = Query(None, description="State parameter for CSRF protection"),
    db: AsyncSession = Depends(get_db),
):
    """
    Google Sheets OAuth callback endpoint.

    Google redirects here after user authorizes the application.
    This endpoint exchanges the authorization code for tokens and saves the connection.
    """
    try:
        print(f"🔵 Google Sheets OAuth Callback - Received code: {code[:20]}...")
        print(f"🔵 State: {state}")

        # Extract tenant_id from state if present
        tenant_id_str = None
        if state and state.startswith("tenant_"):
            tenant_id_str = state.replace("tenant_", "")
            print(f"🔵 Extracted tenant_id: {tenant_id_str}")

        if not tenant_id_str:
            print("❌ Invalid state parameter - no tenant_id")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter",
            )

        # Convert to UUID
        tenant_id = UUID(tenant_id_str)

        # Exchange code for tokens
        print(f"🔵 Exchanging code for tokens...")
        tokens = await GoogleSheetsService.exchange_code_for_tokens(code)
        print(
            f"✅ Tokens received: access_token={tokens['access_token'][:20]}..., has refresh_token={bool(tokens.get('refresh_token'))}"
        )

        # Get tenant to verify it exists
        from app.models.tenant import Tenant

        tenant = await db.get(Tenant, tenant_id)
        if not tenant:
            print(f"❌ Tenant not found: {tenant_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant not found",
            )

        print(f"✅ Tenant found: {tenant.email}")

        # Save connection for the tenant
        print(f"🔵 Saving connection to database...")
        connection = await GoogleSheetsService.save_connection(
            tenant_id=tenant_id,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=tokens["expires_in"],
            scope=tokens.get("scope", ""),
            db=db,
        )
        print(f"✅ Connection saved! ID: {connection.id}")

        # Redirect to frontend success page
        frontend_url = settings.frontend_url
        redirect_url = f"{frontend_url}/chat/inventory?connected=success"
        print(f"🔵 Redirecting to: {redirect_url}")
        return RedirectResponse(url=redirect_url)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in Google Sheets callback: {str(e)}")
        import traceback

        traceback.print_exc()
        # Redirect to frontend error page
        frontend_url = settings.frontend_url
        return RedirectResponse(url=f"{frontend_url}/chat/inventory?error={str(e)}")


@router.get("/status", response_model=GoogleSheetsConnectionStatus)
async def get_connection_status(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current Google Sheets connection status for the tenant.

    Returns connection details including token info and sheet configuration.
    """
    from datetime import datetime

    connection = await GoogleSheetsService.get_active_connection(current_tenant.id, db)

    if not connection:
        return GoogleSheetsConnectionStatus(
            is_connected=False,
            refresh_token=None,
            token_expires_at=None,
            is_token_expired=False,
            inventory_workbook_id=None,
            inventory_worksheet_name=None,
            orders_workbook_id=None,
            orders_worksheet_name=None,
            last_synced_at=None,
        )

    # Check if token is expired
    is_expired = connection.token_expires_at <= datetime.now()

    return GoogleSheetsConnectionStatus(
        is_connected=True,
        refresh_token=connection.refresh_token,
        token_expires_at=connection.token_expires_at,
        is_token_expired=is_expired,
        inventory_workbook_id=connection.inventory_workbook_id,
        inventory_worksheet_name=connection.inventory_worksheet_name,
        orders_workbook_id=connection.orders_workbook_id,
        orders_worksheet_name=connection.orders_worksheet_name,
        last_synced_at=connection.last_synced_at,
    )


@router.get("/spreadsheets", response_model=SpreadsheetsListResponse)
async def list_spreadsheets(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List all Google Sheets spreadsheets accessible to the connected account.

    Requires an active Google Sheets connection.
    """
    access_token = await GoogleSheetsService.get_valid_access_token(
        current_tenant.id, db
    )
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google Sheets not connected. Please connect first.",
        )

    spreadsheets = await GoogleSheetsService.list_spreadsheets(access_token)

    return SpreadsheetsListResponse(
        spreadsheets=[
            SpreadsheetInfo(id=sheet["id"], name=sheet["name"])
            for sheet in spreadsheets
        ]
    )


@router.get(
    "/spreadsheets/{spreadsheet_id}/worksheets", response_model=WorksheetsListResponse
)
async def list_worksheets(
    spreadsheet_id: str,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    List all worksheets/tabs in a specific Google Spreadsheet.

    Requires an active Google Sheets connection.
    """
    access_token = await GoogleSheetsService.get_valid_access_token(
        current_tenant.id, db
    )
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google Sheets not connected. Please connect first.",
        )

    worksheets = await GoogleSheetsService.list_worksheets(spreadsheet_id, access_token)

    return WorksheetsListResponse(
        worksheets=[
            WorksheetInfo(
                name=ws["name"],
                index=ws["index"],
                row_count=ws["row_count"],
                column_count=ws["column_count"],
            )
            for ws in worksheets
        ]
    )


@router.post("/config", response_model=GoogleSheetsConnectionStatus)
async def save_sheet_config(
    config: SaveSheetsConfigRequest,
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Save Google Sheets configuration for inventory and orders.

    Specifies which spreadsheet and worksheet to use for inventory and orders tracking.
    """
    from datetime import datetime

    connection = await GoogleSheetsService.save_sheet_config(
        tenant_id=current_tenant.id,
        inventory_workbook_id=config.inventory.workbook_id,
        inventory_worksheet_name=config.inventory.worksheet_name,
        orders_workbook_id=config.orders.workbook_id,
        orders_worksheet_name=config.orders.worksheet_name,
        db=db,
    )

    # Check if token is expired
    is_expired = connection.token_expires_at <= datetime.now()

    return GoogleSheetsConnectionStatus(
        is_connected=True,
        refresh_token=connection.refresh_token,
        token_expires_at=connection.token_expires_at,
        is_token_expired=is_expired,
        inventory_workbook_id=connection.inventory_workbook_id,
        inventory_worksheet_name=connection.inventory_worksheet_name,
        orders_workbook_id=connection.orders_workbook_id,
        orders_worksheet_name=connection.orders_worksheet_name,
        last_synced_at=connection.last_synced_at,
    )


@router.post("/disconnect", response_model=GoogleSheetsDisconnectResponse)
async def disconnect_google_sheets(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Disconnect Google Sheets integration for the current tenant.

    Deactivates the connection but preserves the configuration.
    """
    await GoogleSheetsService.disconnect(current_tenant.id, db)

    return GoogleSheetsDisconnectResponse(
        message="Google Sheets disconnected successfully",
        disconnected=True,
    )


@router.get("/orders", response_model=OrdersDataResponse)
async def get_orders_data(
    current_tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Get orders data from the configured Orders sheet.

    Fetches data from the Google Sheets Orders worksheet configured for this tenant.
    Parses the data and returns structured orders with calculated statistics.
    """
    data = await GoogleSheetsService.get_orders_data(current_tenant.id, db)

    return OrdersDataResponse(
        orders=[OrderItem(**order) for order in data["orders"]],
        stats=OrdersStats(**data["stats"]),
        last_synced_at=data["last_synced_at"],
    )
