"""
QuickBooks OAuth service
Handles QuickBooks OAuth2 integration and API calls
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
import httpx
from urllib.parse import urlencode

from app.core.config import settings
from app.models.quickbooks_connection import QuickBooksConnection


class QuickBooksService:
    """Service for QuickBooks OAuth and API operations"""

    # QuickBooks OAuth endpoints
    AUTHORIZATION_ENDPOINT = "https://appcenter.intuit.com/connect/oauth2"
    TOKEN_ENDPOINT = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    REVOKE_ENDPOINT = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
    API_BASE_URL = "https://quickbooks.api.intuit.com/v3"

    # Sandbox endpoints (use these for development/testing)
    SANDBOX_API_BASE_URL = "https://sandbox-quickbooks.api.intuit.com/v3"

    @staticmethod
    def get_authorization_url(state: Optional[str] = None) -> str:
        """
        Generate QuickBooks OAuth authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL to redirect user to
        """
        params = {
            "client_id": settings.quickbooks_client_id,
            "redirect_uri": settings.quickbooks_redirect_uri,
            "response_type": "code",
            "scope": settings.quickbooks_scopes,
            "state": state or "quickbooks_oauth",
        }
        return f"{QuickBooksService.AUTHORIZATION_ENDPOINT}?{urlencode(params)}"

    @staticmethod
    async def exchange_code_for_tokens(code: str, realm_id: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from callback
            realm_id: QuickBooks Company ID (realmId)

        Returns:
            Dictionary containing access_token, refresh_token, and expires_in
        """
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.quickbooks_redirect_uri,
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                QuickBooksService.TOKEN_ENDPOINT,
                data=token_data,
                headers=headers,
                auth=(settings.quickbooks_client_id, settings.quickbooks_client_secret),
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange code for tokens: {response.text}",
                )

            return response.json()

    @staticmethod
    async def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Current refresh token

        Returns:
            Dictionary containing new access_token, refresh_token, and expires_in
        """
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                QuickBooksService.TOKEN_ENDPOINT,
                data=token_data,
                headers=headers,
                auth=(settings.quickbooks_client_id, settings.quickbooks_client_secret),
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Failed to refresh access token",
                )

            return response.json()

    @staticmethod
    async def get_company_info(
        access_token: str, realm_id: str, use_sandbox: bool = False
    ) -> Dict[str, Any]:
        """
        Get QuickBooks company information.

        Args:
            access_token: Valid access token
            realm_id: QuickBooks Company ID
            use_sandbox: Whether to use sandbox environment

        Returns:
            Company information from QuickBooks API
        """
        base_url = (
            QuickBooksService.SANDBOX_API_BASE_URL
            if use_sandbox
            else QuickBooksService.API_BASE_URL
        )
        url = f"{base_url}/company/{realm_id}/companyinfo/{realm_id}"

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to get company info: {response.text}",
                )

            return response.json()

    @staticmethod
    async def save_connection(
        tenant_id: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        realm_id: str,
        db: AsyncSession,
    ) -> QuickBooksConnection:
        """
        Save or update QuickBooks connection for a tenant.

        Args:
            tenant_id: Tenant/Organization ID
            access_token: QuickBooks access token
            refresh_token: QuickBooks refresh token
            expires_in: Token expiration time in seconds
            realm_id: QuickBooks Company ID
            db: Database session

        Returns:
            QuickBooksConnection object
        """
        # Check if connection already exists for this tenant
        statement = select(QuickBooksConnection).where(
            QuickBooksConnection.tenant_id == tenant_id
        )
        result = await db.exec(statement)
        connection = result.first()

        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        # Get company info
        try:
            company_data = await QuickBooksService.get_company_info(
                access_token, realm_id, use_sandbox=settings.quickbooks_use_sandbox
            )
            company_info = company_data.get("CompanyInfo", {})
            company_name = company_info.get("CompanyName")
            company_country = company_info.get("Country")
            company_currency = company_info.get("CompanyAddr", {}).get(
                "Country"
            ) or company_info.get("Country")
        except Exception as e:
            # If we can't get company info, just save the connection without it
            company_name = None
            company_country = None
            company_currency = None

        if connection:
            # Update existing connection
            connection.access_token = access_token
            connection.refresh_token = refresh_token
            connection.token_expires_at = expires_at
            connection.realm_id = realm_id
            connection.company_name = company_name
            connection.company_country = company_country
            connection.company_currency = company_currency
            connection.is_active = True
            connection.last_synced_at = datetime.utcnow()
        else:
            # Create new connection
            connection = QuickBooksConnection(
                tenant_id=tenant_id,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=expires_at,
                realm_id=realm_id,
                company_name=company_name,
                company_country=company_country,
                company_currency=company_currency,
                is_active=True,
                last_synced_at=datetime.utcnow(),
                scopes=settings.quickbooks_scopes,
            )

        db.add(connection)
        await db.commit()
        await db.refresh(connection)
        return connection

    @staticmethod
    async def get_tenant_connection(
        tenant_id: str, db: AsyncSession
    ) -> Optional[QuickBooksConnection]:
        """
        Get QuickBooks connection for a tenant.

        Args:
            tenant_id: Tenant ID
            db: Database session

        Returns:
            QuickBooksConnection if exists, None otherwise
        """
        statement = select(QuickBooksConnection).where(
            QuickBooksConnection.tenant_id == tenant_id,
            QuickBooksConnection.is_active == True,
        )
        result = await db.exec(statement)
        return result.first()

    @staticmethod
    async def disconnect(tenant_id: str, db: AsyncSession) -> bool:
        """
        Disconnect QuickBooks for a tenant (revoke tokens and mark inactive).

        Args:
            tenant_id: Tenant ID
            db: Database session

        Returns:
            True if successful, False otherwise
        """
        connection = await QuickBooksService.get_tenant_connection(tenant_id, db)

        if not connection:
            return False

        # Try to revoke the token with QuickBooks
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    QuickBooksService.REVOKE_ENDPOINT,
                    json={"token": connection.refresh_token},
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                    auth=(
                        settings.quickbooks_client_id,
                        settings.quickbooks_client_secret,
                    ),
                )
        except Exception:
            # If revocation fails, still mark as inactive locally
            pass

        # Mark connection as inactive
        connection.is_active = False
        db.add(connection)
        await db.commit()
        return True

    @staticmethod
    async def ensure_valid_token(
        connection: QuickBooksConnection, db: AsyncSession
    ) -> str:
        """
        Ensure the access token is valid, refresh if needed.

        Args:
            connection: QuickBooksConnection object
            db: Database session

        Returns:
            Valid access token
        """
        # Check if token is expired or will expire in next 5 minutes
        if datetime.utcnow() + timedelta(minutes=5) >= connection.token_expires_at:
            # Refresh the token
            tokens = await QuickBooksService.refresh_access_token(
                connection.refresh_token
            )

            # Update connection
            connection.access_token = tokens["access_token"]
            connection.refresh_token = tokens["refresh_token"]
            connection.token_expires_at = datetime.utcnow() + timedelta(
                seconds=tokens["expires_in"]
            )

            db.add(connection)
            await db.commit()
            await db.refresh(connection)

        return connection.access_token
