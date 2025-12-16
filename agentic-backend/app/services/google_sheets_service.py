"""
Google Sheets Service

Handles Google Sheets OAuth flow and API interactions including:
- OAuth authorization and token exchange
- Token refresh
- Fetching spreadsheets and worksheets
- Saving and retrieving connection configuration
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
import httpx
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from urllib.parse import urlencode

from app.models.google_sheets_connection import GoogleSheetsConnection
from app.core.config import settings


class GoogleSheetsService:
    """Service for managing Google Sheets OAuth and API operations"""

    # Token refresh buffer - refresh 5 minutes before actual expiry
    TOKEN_REFRESH_BUFFER = timedelta(minutes=5)

    # Google OAuth endpoints
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_DRIVE_API = "https://www.googleapis.com/drive/v3"
    GOOGLE_SHEETS_API = "https://sheets.googleapis.com/v4"

    @staticmethod
    def get_authorization_url(state: str) -> str:
        """
        Generate Google OAuth authorization URL.

        Args:
            state: State parameter to prevent CSRF (typically tenant_id)

        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "client_id": settings.google_sheets_client_id,
            "redirect_uri": settings.google_sheets_redirect_uri,
            "response_type": "code",
            "scope": settings.google_sheets_scopes,
            "access_type": "offline",  # Required to get refresh token
            "prompt": "consent",  # Force consent screen to ensure refresh token
            "state": state,
        }
        return f"{GoogleSheetsService.GOOGLE_AUTH_URL}?{urlencode(params)}"

    @staticmethod
    async def exchange_code_for_tokens(code: str) -> dict:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth callback

        Returns:
            Dictionary containing access_token, refresh_token, expires_in, etc.

        Raises:
            HTTPException if token exchange fails
        """
        from fastapi import HTTPException, status

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    GoogleSheetsService.GOOGLE_TOKEN_URL,
                    data={
                        "code": code,
                        "client_id": settings.google_sheets_client_id,
                        "client_secret": settings.google_sheets_client_secret,
                        "redirect_uri": settings.google_sheets_redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange code for tokens: {e.response.text}",
                )

    @staticmethod
    async def save_connection(
        tenant_id: UUID,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        scope: str,
        db: AsyncSession,
    ) -> GoogleSheetsConnection:
        """
        Save or update Google Sheets connection for a tenant.

        Args:
            tenant_id: Tenant UUID
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_in: Token expiry time in seconds
            scope: Granted OAuth scopes
            db: Database session

        Returns:
            Saved GoogleSheetsConnection object
        """
        # Check if connection already exists
        statement = select(GoogleSheetsConnection).where(
            GoogleSheetsConnection.tenant_id == tenant_id
        )
        result = await db.execute(statement)
        connection = result.scalar_one_or_none()

        # Use timezone-naive datetime for PostgreSQL compatibility
        token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        if connection:
            # Update existing connection
            connection.access_token = access_token
            connection.refresh_token = refresh_token
            connection.token_expires_at = token_expires_at
            connection.scopes = scope
            connection.is_active = True
        else:
            # Create new connection
            connection = GoogleSheetsConnection(
                tenant_id=tenant_id,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=token_expires_at,
                scopes=scope,
                is_active=True,
            )
            db.add(connection)

        await db.commit()
        await db.refresh(connection)
        return connection

    @staticmethod
    async def get_active_connection(
        tenant_id: UUID, db: AsyncSession
    ) -> Optional[GoogleSheetsConnection]:
        """
        Get active Google Sheets connection for a tenant.

        Args:
            tenant_id: Tenant UUID
            db: Database session

        Returns:
            GoogleSheetsConnection if found and active, None otherwise
        """
        statement = select(GoogleSheetsConnection).where(
            GoogleSheetsConnection.tenant_id == tenant_id,
            GoogleSheetsConnection.is_active == True,
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def refresh_access_token(
        connection: GoogleSheetsConnection, db: AsyncSession
    ) -> str:
        """
        Refresh Google OAuth access token using refresh token.

        Args:
            connection: Google Sheets connection object
            db: Database session

        Returns:
            New access token

        Raises:
            HTTPException if token refresh fails
        """
        from fastapi import HTTPException, status

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    GoogleSheetsService.GOOGLE_TOKEN_URL,
                    data={
                        "refresh_token": connection.refresh_token,
                        "client_id": settings.google_sheets_client_id,
                        "client_secret": settings.google_sheets_client_secret,
                        "grant_type": "refresh_token",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
                token_data = response.json()

                # Update connection with new token
                connection.access_token = token_data["access_token"]
                connection.token_expires_at = datetime.now() + timedelta(
                    seconds=token_data["expires_in"]
                )
                await db.commit()
                await db.refresh(connection)

                return token_data["access_token"]

            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Failed to refresh token: {e.response.text}",
                )

    @staticmethod
    async def get_valid_access_token(
        tenant_id: UUID, db: AsyncSession
    ) -> Optional[str]:
        """
        Get a valid access token for a tenant, refreshing if necessary.

        Args:
            tenant_id: Tenant UUID
            db: Database session

        Returns:
            Valid access token or None if no connection exists
        """
        connection = await GoogleSheetsService.get_active_connection(tenant_id, db)
        if not connection:
            return None

        # Check if token is expired or about to expire
        now = datetime.now()
        if (
            connection.token_expires_at
            <= now + GoogleSheetsService.TOKEN_REFRESH_BUFFER
        ):
            # Token expired or about to expire, refresh it
            return await GoogleSheetsService.refresh_access_token(connection, db)

        return connection.access_token

    @staticmethod
    async def list_spreadsheets(access_token: str) -> list[dict]:
        """
        List Google Sheets spreadsheets accessible to the user.

        Args:
            access_token: Valid OAuth access token

        Returns:
            List of spreadsheet dictionaries with id and name

        Raises:
            HTTPException if API call fails
        """
        from fastapi import HTTPException, status

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{GoogleSheetsService.GOOGLE_DRIVE_API}/files",
                    params={
                        "q": "mimeType='application/vnd.google-apps.spreadsheet'",
                        "fields": "files(id, name)",
                        "pageSize": 100,
                    },
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("files", [])
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to list spreadsheets: {e.response.text}",
                )

    @staticmethod
    async def list_worksheets(spreadsheet_id: str, access_token: str) -> list[dict]:
        """
        List worksheets/tabs in a Google Spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            access_token: Valid OAuth access token

        Returns:
            List of worksheet dictionaries with title, index, dimensions

        Raises:
            HTTPException if API call fails
        """
        from fastapi import HTTPException, status

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{GoogleSheetsService.GOOGLE_SHEETS_API}/spreadsheets/{spreadsheet_id}",
                    params={"fields": "sheets.properties"},
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                data = response.json()

                worksheets = []
                for sheet in data.get("sheets", []):
                    props = sheet["properties"]
                    worksheets.append(
                        {
                            "name": props["title"],
                            "index": props["index"],
                            "row_count": props["gridProperties"]["rowCount"],
                            "column_count": props["gridProperties"]["columnCount"],
                        }
                    )
                return worksheets
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to list worksheets: {e.response.text}",
                )

    @staticmethod
    async def save_sheet_config(
        tenant_id: UUID,
        inventory_workbook_id: str,
        inventory_worksheet_name: str,
        orders_workbook_id: str,
        orders_worksheet_name: str,
        db: AsyncSession,
    ) -> GoogleSheetsConnection:
        """
        Save sheet configuration for inventory and orders.

        Args:
            tenant_id: Tenant UUID
            inventory_workbook_id: Inventory spreadsheet ID
            inventory_worksheet_name: Inventory worksheet name
            orders_workbook_id: Orders spreadsheet ID
            orders_worksheet_name: Orders worksheet name
            db: Database session

        Returns:
            Updated GoogleSheetsConnection object

        Raises:
            HTTPException if connection not found
        """
        from fastapi import HTTPException, status

        connection = await GoogleSheetsService.get_active_connection(tenant_id, db)
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Google Sheets connection not found. Please connect first.",
            )

        # Update sheet configuration
        connection.inventory_workbook_id = inventory_workbook_id
        connection.inventory_worksheet_name = inventory_worksheet_name
        connection.orders_workbook_id = orders_workbook_id
        connection.orders_worksheet_name = orders_worksheet_name
        connection.last_synced_at = datetime.now()

        await db.commit()
        await db.refresh(connection)
        return connection

    @staticmethod
    async def read_worksheet_data(
        spreadsheet_id: str, worksheet_name: str, access_token: str
    ) -> list[list[str]]:
        """
        Read all data from a worksheet.

        Args:
            spreadsheet_id: Spreadsheet ID
            worksheet_name: Name of the worksheet/tab
            access_token: Valid OAuth access token

        Returns:
            List of rows, where each row is a list of cell values

        Raises:
            HTTPException if API call fails
        """
        from fastapi import HTTPException, status

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{GoogleSheetsService.GOOGLE_SHEETS_API}/spreadsheets/{spreadsheet_id}/values/{worksheet_name}",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("values", [])
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to read worksheet data: {e.response.text}",
                )

    @staticmethod
    async def get_orders_data(
        tenant_id: UUID, db: AsyncSession
    ) -> dict:
        """
        Get orders data from the configured Orders sheet for a tenant.

        Args:
            tenant_id: Tenant UUID
            db: Database session

        Returns:
            Dictionary with orders data, stats, and metadata

        Raises:
            HTTPException if connection not found or sheet not configured
        """
        from fastapi import HTTPException, status

        connection = await GoogleSheetsService.get_active_connection(tenant_id, db)
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Google Sheets connection not found. Please connect first.",
            )

        if not connection.orders_workbook_id or not connection.orders_worksheet_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Orders sheet not configured. Please configure the Orders sheet first.",
            )

        # Get valid access token
        access_token = await GoogleSheetsService.get_valid_access_token(tenant_id, db)
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to get valid access token",
            )

        # Read data from the Orders sheet
        raw_data = await GoogleSheetsService.read_worksheet_data(
            connection.orders_workbook_id,
            connection.orders_worksheet_name,
            access_token,
        )

        if not raw_data:
            return {
                "orders": [],
                "stats": {
                    "total_revenue": 0,
                    "completed_count": 0,
                    "pending_count": 0,
                },
                "last_synced_at": datetime.now().isoformat(),
            }

        # Parse orders data - assume first row is headers
        headers = raw_data[0] if raw_data else []
        orders = []
        total_revenue = 0
        completed_count = 0
        pending_count = 0

        # Map common header variations to standard names
        header_map = {}
        for idx, header in enumerate(headers):
            header_lower = header.lower().strip()
            if header_lower in ["date", "order_date", "order date", "created_at"]:
                header_map["date"] = idx
            elif header_lower in ["customer", "customer_name", "customer name", "name", "buyer"]:
                header_map["customer"] = idx
            elif header_lower in ["amount", "total", "price", "value", "order_amount"]:
                header_map["amount"] = idx
            elif header_lower in ["method", "payment_method", "payment method", "payment"]:
                header_map["method"] = idx
            elif header_lower in ["status", "order_status", "payment_status", "state"]:
                header_map["status"] = idx
            elif header_lower in ["id", "order_id", "order id"]:
                header_map["id"] = idx

        # Parse each data row
        for row_idx, row in enumerate(raw_data[1:], start=1):
            if not row:  # Skip empty rows
                continue

            order = {
                "id": str(row_idx),
                "date": "",
                "customer": "",
                "amount": 0,
                "amount_display": "",
                "method": "",
                "status": "pending",
            }

            # Extract values based on header mapping
            if "id" in header_map and len(row) > header_map["id"]:
                order["id"] = row[header_map["id"]]
            if "date" in header_map and len(row) > header_map["date"]:
                order["date"] = row[header_map["date"]]
            if "customer" in header_map and len(row) > header_map["customer"]:
                order["customer"] = row[header_map["customer"]]
            if "amount" in header_map and len(row) > header_map["amount"]:
                amount_str = row[header_map["amount"]]
                # Try to extract numeric value
                try:
                    # Remove currency symbols and commas
                    clean_amount = "".join(c for c in amount_str if c.isdigit() or c == ".")
                    order["amount"] = float(clean_amount) if clean_amount else 0
                    order["amount_display"] = amount_str
                except ValueError:
                    order["amount"] = 0
                    order["amount_display"] = amount_str
            if "method" in header_map and len(row) > header_map["method"]:
                order["method"] = row[header_map["method"]]
            if "status" in header_map and len(row) > header_map["status"]:
                status_val = row[header_map["status"]].lower().strip()
                if status_val in ["completed", "paid", "done", "success", "successful"]:
                    order["status"] = "completed"
                elif status_val in ["pending", "waiting", "processing", "in progress"]:
                    order["status"] = "pending"
                elif status_val in ["failed", "cancelled", "canceled", "refunded"]:
                    order["status"] = "failed"
                else:
                    order["status"] = status_val

            orders.append(order)

            # Calculate stats
            if order["status"] == "completed":
                completed_count += 1
                total_revenue += order["amount"]
            elif order["status"] == "pending":
                pending_count += 1

        # Update last synced timestamp
        last_synced = datetime.now()
        connection.last_synced_at = last_synced
        await db.commit()

        return {
            "orders": orders,
            "stats": {
                "total_revenue": total_revenue,
                "completed_count": completed_count,
                "pending_count": pending_count,
            },
            "last_synced_at": last_synced.isoformat(),
        }

    @staticmethod
    async def disconnect(tenant_id: UUID, db: AsyncSession) -> bool:
        """
        Disconnect Google Sheets for a tenant.

        Args:
            tenant_id: Tenant UUID
            db: Database session

        Returns:
            True if disconnected successfully

        Raises:
            HTTPException if connection not found
        """
        from fastapi import HTTPException, status

        connection = await GoogleSheetsService.get_active_connection(tenant_id, db)
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Google Sheets connection not found",
            )

        connection.is_active = False
        await db.commit()
        return True
