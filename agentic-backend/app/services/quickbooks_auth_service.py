"""
QuickBooks Authentication Service

Manages QuickBooks OAuth tokens including:
- Fetching credentials from database
- Checking token expiry
- Refreshing expired tokens
- Updating tokens in database

Designed for high performance with async operations and minimal DB queries.
"""

from datetime import datetime, timedelta, UTC
from typing import Optional
from uuid import UUID
import httpx
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.quickbooks_connection import QuickBooksConnection
from app.core.config import settings


class QuickBooksAuthService:
    """
    Service for managing QuickBooks OAuth authentication and token refresh.

    This service handles:
    1. Retrieving tenant's QuickBooks credentials from database
    2. Checking if access token is expired or about to expire
    3. Refreshing tokens using QuickBooks OAuth refresh flow
    4. Updating refreshed tokens back to database
    """

    # Token refresh buffer - refresh 5 minutes before actual expiry
    TOKEN_REFRESH_BUFFER = timedelta(minutes=5)

    # QuickBooks OAuth endpoints
    QB_TOKEN_ENDPOINT = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

    def __init__(self, db: AsyncSession):
        """
        Initialize the auth service.

        Args:
            db: Async database session for querying/updating credentials
        """
        self.db = db

    async def get_active_connection(
        self, tenant_id: UUID
    ) -> Optional[QuickBooksConnection]:
        """
        Get active QuickBooks connection for a tenant.

        Args:
            tenant_id: UUID of the tenant

        Returns:
            QuickBooksConnection if found and active, None otherwise
        """
        statement = select(QuickBooksConnection).where(
            QuickBooksConnection.tenant_id == tenant_id,
            QuickBooksConnection.is_active == True,
        )
        result = await self.db.execute(statement)
        return result.scalar_one_or_none()

    async def get_valid_credentials(self, tenant_id: UUID) -> Optional[dict[str, str]]:
        """
        Get valid QuickBooks credentials for a tenant, refreshing if needed.

        This is the main method to use when you need QuickBooks credentials.
        It handles the entire flow:
        1. Fetch connection from DB
        2. Check if token is expired or about to expire
        3. Refresh token if needed
        4. Return credentials (even if refresh fails, let QB API handle it)

        Args:
            tenant_id: UUID of the tenant

        Returns:
            Dictionary with 'access_token' and 'realm_id' if available, None otherwise

        Example:
            creds = await service.get_valid_credentials(tenant_id)
            if creds:
                access_token = creds['access_token']
                realm_id = creds['realm_id']
        """
        # Get connection from database (including inactive ones now)
        statement = select(QuickBooksConnection).where(
            QuickBooksConnection.tenant_id == tenant_id
        )
        result = await self.db.execute(statement)
        connection = result.scalar_one_or_none()

        if not connection:
            # Tenant has no QuickBooks connection
            return None

        # Check if token needs refresh
        if self._should_refresh_token(connection):
            # Token is expired or about to expire - try to refresh it
            print(f"🔄 Refreshing QuickBooks token for tenant {tenant_id}...")
            success = await self._refresh_access_token(connection)

            if not success:
                # Refresh failed (likely refresh token expired after ~100 days)
                # Mark connection as inactive so user knows to reconnect
                print(
                    f"⚠️  Refresh token expired for tenant {tenant_id} - marking connection as inactive"
                )

                # Create a fresh database session to avoid transaction conflicts
                from app.utils.db import engine
                from sqlmodel.ext.asyncio.session import AsyncSession

                async with AsyncSession(engine) as fresh_db:
                    # Get connection in this fresh session
                    result = await fresh_db.execute(
                        select(QuickBooksConnection).where(
                            QuickBooksConnection.tenant_id == tenant_id,
                            QuickBooksConnection.is_active == True,
                        )
                    )
                    conn_to_update = result.scalar_one_or_none()

                    if conn_to_update:
                        conn_to_update.is_active = False
                        fresh_db.add(conn_to_update)
                        await fresh_db.commit()

                # Return None to indicate connection needs to be re-established
                return None

        # Return credentials regardless of refresh status
        # If token is invalid, QuickBooks API will return 401 and user can reconnect
        return {
            "access_token": connection.access_token,
            "realm_id": connection.realm_id,
        }

    def _should_refresh_token(self, connection: QuickBooksConnection) -> bool:
        """
        Check if token should be refreshed.

        Tokens are refreshed if they are expired or will expire within
        the TOKEN_REFRESH_BUFFER window.

        Args:
            connection: QuickBooks connection to check

        Returns:
            True if token should be refreshed, False otherwise
        """
        now = datetime.now(UTC)

        # Make token_expires_at timezone-aware if it isn't
        expires_at = connection.token_expires_at
        if expires_at.tzinfo is None:
            # Assume UTC if no timezone info
            expires_at = expires_at.replace(tzinfo=UTC)

        # Refresh if token is expired or will expire soon
        return now >= (expires_at - self.TOKEN_REFRESH_BUFFER)

    async def _refresh_access_token(self, connection: QuickBooksConnection) -> bool:
        """
        Refresh QuickBooks access token using refresh token.

        Args:
            connection: QuickBooks connection with refresh token

        Returns:
            True if refresh succeeded, False otherwise
        """
        try:
            # Prepare refresh token request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.QB_TOKEN_ENDPOINT,
                    headers={
                        "Accept": "application/json",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    auth=(
                        settings.quickbooks_client_id,
                        settings.quickbooks_client_secret,
                    ),
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": connection.refresh_token,
                    },
                    timeout=10.0,
                )

                if response.status_code != 200:
                    print(
                        f"❌ QuickBooks token refresh failed for tenant {connection.tenant_id}: "
                        f"Status {response.status_code}"
                    )
                    return False

                # Parse response
                token_data = response.json()

                # Store tenant_id before potential rollback
                tenant_id_for_logging = connection.tenant_id

                # Update connection with new tokens
                connection.access_token = token_data["access_token"]
                connection.refresh_token = token_data["refresh_token"]

                # Calculate new expiry time (timezone-naive for PostgreSQL TIMESTAMP WITHOUT TIME ZONE)
                expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
                connection.token_expires_at = datetime.utcnow() + timedelta(
                    seconds=expires_in
                )

                # Save to database
                self.db.add(connection)
                await self.db.commit()
                await self.db.refresh(connection)

                print(
                    f"✅ QuickBooks token refreshed for tenant {tenant_id_for_logging}, "
                    f"expires at {connection.token_expires_at}"
                )
                return True

        except httpx.HTTPError as e:
            # Store tenant_id before accessing connection attributes (might be expired after error)
            tenant_id_for_logging = getattr(connection, "tenant_id", "unknown")
            print(
                f"❌ QuickBooks token refresh HTTP error for tenant {tenant_id_for_logging}: {e}"
            )
            return False
        except Exception as e:
            # Store tenant_id before accessing connection attributes (might be expired after error)
            tenant_id_for_logging = getattr(connection, "tenant_id", "unknown")
            print(
                f"❌ QuickBooks token refresh unexpected error for tenant {tenant_id_for_logging}: {e}"
            )
            return False

    async def validate_and_refresh_if_needed(
        self, tenant_id: UUID
    ) -> tuple[bool, Optional[str]]:
        """
        Validate credentials and return status.

        Args:
            tenant_id: UUID of the tenant

        Returns:
            Tuple of (is_valid, error_message)
        """
        connection = await self.get_active_connection(tenant_id)

        if not connection:
            return False, "No QuickBooks connection found for tenant"

        if self._should_refresh_token(connection):
            success = await self._refresh_access_token(connection)
            if not success:
                return False, "Token refresh failed - credentials may be invalid"

        return True, None


# Convenience function for getting credentials without creating service instance
async def get_quickbooks_credentials(
    tenant_id: UUID, db: AsyncSession
) -> Optional[dict[str, str]]:
    """
    Convenience function to get QuickBooks credentials for a tenant.

    This is a shorthand for creating the service and calling get_valid_credentials.

    Args:
        tenant_id: UUID of the tenant
        db: Database session

    Returns:
        Dictionary with 'access_token' and 'realm_id' if available, None otherwise
    """
    service = QuickBooksAuthService(db)
    return await service.get_valid_credentials(tenant_id)
