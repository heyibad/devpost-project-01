"""
Unified MCP Manager

ONE place to manage ALL MCP connections:
- QuickBooks (per-tenant with dynamic credentials)
- Stripe, Shopify, etc. (per-tenant with dynamic credentials)
- Generic global tools (shared, no credentials)

This replaces the messy multi-file approach with a single, clean system.

CONCURRENCY FIXES:
- Thread-safe exit stack initialization
- Per-tenant locking to avoid blocking other tenants
- Request-scoped connection sharing to avoid duplicate connections
- Failed connection TTL to allow automatic retries
"""

from contextlib import AsyncExitStack
from contextvars import ContextVar
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta, UTC
import asyncio

from agents.mcp import (
    MCPServerStreamableHttp,
    MCPServerStreamableHttpParams,
    create_static_tool_filter,
)
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.config import settings


# Request-scoped connection cache using contextvars
# This allows multiple agents in the same request to share the same MCP connection
_request_global_mcp: ContextVar[dict[UUID, MCPServerStreamableHttp]] = ContextVar(
    "request_global_mcp", default={}
)


class UnifiedMCPManager:
    """
    Single manager for ALL MCP connections with intelligent connection pooling.

    Handles:
    - QuickBooks connections (per-tenant, dynamic credentials)
    - Other service connections (Stripe, Shopify, etc.)
    - Generic shared tools (no credentials needed)

    Connection Pooling Strategy:
    - Keeps connections alive in a long-lived AsyncExitStack
    - Caches connections for reuse across requests (reduces latency)
    - Validates connections are still alive before reusing
    - Invalidates and recreates on token refresh or connection errors
    - Proper cleanup on shutdown
    """

    def __init__(self):
        self._exit_stack: Optional[AsyncExitStack] = None
        self._exit_stack_lock = (
            asyncio.Lock()
        )  # FIX: Lock for exit stack initialization
        self._tenant_connections: dict[UUID, dict] = (
            {}
        )  # {tenant_id: {"quickbooks": mcp, "global": mcp}}
        self._tenant_tokens: dict[UUID, str] = (
            {}
        )  # {tenant_id: access_token} for change detection
        self._connection_created_at: dict[UUID, dict[str, datetime]] = (
            {}
        )  # Track when connections were created
        # FIX: Track failed connections with timestamps for automatic retry after TTL
        self._failed_connections: dict[UUID, dict[str, datetime]] = (
            {}
        )  # {tenant_id: {"quickbooks": timestamp, "global": timestamp}}
        self._failed_connection_ttl = timedelta(
            seconds=30
        )  # FIX: Retry failed connections after 30s
        self._locks: dict[UUID, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()
        self._max_connection_age = timedelta(minutes=30)  # Refresh after 30 minutes

        # PERFORMANCE: Cache credentials to avoid DB queries on every request
        self._quickbooks_creds_cache: dict[UUID, Optional[dict]] = (
            {}
        )  # {tenant_id: creds}
        self._sheets_creds_cache: dict[UUID, Optional[dict]] = {}  # {tenant_id: creds}
        self._creds_cache_ttl = timedelta(minutes=5)  # Refresh cache every 5 minutes
        self._creds_cache_timestamps: dict[UUID, dict[str, datetime]] = (
            {}
        )  # Track cache age

    async def _ensure_exit_stack(self):
        """Initialize exit stack if needed - thread-safe."""
        # FIX: Use lock to prevent race condition where multiple concurrent requests
        # create multiple exit stacks (only first one should create)
        async with self._exit_stack_lock:
            if self._exit_stack is None:
                self._exit_stack = AsyncExitStack()
                await self._exit_stack.__aenter__()
                print("✅ Initialized global AsyncExitStack for MCP connections")

    async def _get_tenant_lock(self, tenant_id: UUID) -> asyncio.Lock:
        """Get or create a lock for a specific tenant."""
        async with self._global_lock:
            if tenant_id not in self._locks:
                self._locks[tenant_id] = asyncio.Lock()
            return self._locks[tenant_id]

    def _is_connection_stale(self, tenant_id: UUID, connection_type: str) -> bool:
        """Check if a connection is too old and should be refreshed."""
        if tenant_id not in self._connection_created_at:
            return True
        if connection_type not in self._connection_created_at[tenant_id]:
            return True

        created_at = self._connection_created_at[tenant_id][connection_type]
        age = datetime.now(UTC) - created_at
        return age > self._max_connection_age

    async def _invalidate_connection(
        self, tenant_id: UUID, connection_type: str
    ) -> None:
        """Invalidate a cached connection (doesn't close it, just removes from cache)."""
        if tenant_id in self._tenant_connections:
            self._tenant_connections[tenant_id].pop(connection_type, None)
        if tenant_id in self._connection_created_at:
            self._connection_created_at[tenant_id].pop(connection_type, None)
        if tenant_id in self._failed_connections:
            self._failed_connections[tenant_id].pop(connection_type, None)
        print(f"🗑️  Invalidated {connection_type} connection for tenant {tenant_id}")

    def _is_failure_expired(self, tenant_id: UUID, connection_type: str) -> bool:
        """Check if a failed connection's TTL has expired and should be retried."""
        if tenant_id not in self._failed_connections:
            return True
        if connection_type not in self._failed_connections[tenant_id]:
            return True

        failed_at = self._failed_connections[tenant_id][connection_type]
        age = datetime.now(UTC) - failed_at
        return age > self._failed_connection_ttl

    def _mark_connection_failed(self, tenant_id: UUID, connection_type: str) -> None:
        """Mark a connection as failed with current timestamp."""
        if tenant_id not in self._failed_connections:
            self._failed_connections[tenant_id] = {}
        self._failed_connections[tenant_id][connection_type] = datetime.now(UTC)
        print(
            f"⚠️  Marked {connection_type} as failed for tenant {tenant_id} (will retry after {self._failed_connection_ttl.seconds}s)"
        )

    # ========================================================================
    # QuickBooks MCP (Port 8002) - ONLY for Accounts Agent
    # ========================================================================

    def _is_creds_cache_stale(self, tenant_id: UUID, creds_type: str) -> bool:
        """Check if cached credentials are too old."""
        if tenant_id not in self._creds_cache_timestamps:
            return True
        if creds_type not in self._creds_cache_timestamps[tenant_id]:
            return True

        cached_at = self._creds_cache_timestamps[tenant_id][creds_type]
        age = datetime.now(UTC) - cached_at
        return age > self._creds_cache_ttl

    async def get_quickbooks_mcp(
        self,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> Optional[MCPServerStreamableHttp]:
        """
        Get QuickBooks MCP server for a tenant (Port 8002).

        ONLY for Accounts Agent. Returns None if tenant has no QB credentials.

        Handles token refresh:
        - Checks credentials FIRST (before cache)
        - Detects if access token changed (refreshed)
        - Invalidates cache and recreates MCP if token changed

        Returns:
            MCP server with QB tools, or None if tenant has no QB connection
        """
        from app.services.quickbooks_auth_service import get_quickbooks_credentials

        lock = await self._get_tenant_lock(tenant_id)

        async with lock:
            # STEP 1: Get credentials - use cache first to avoid DB query
            creds = None
            if (
                tenant_id in self._quickbooks_creds_cache
                and not self._is_creds_cache_stale(tenant_id, "quickbooks")
            ):
                creds = self._quickbooks_creds_cache[tenant_id]
                print(f"⚡ Using cached QuickBooks credentials for tenant {tenant_id}")
            else:
                # Fetch from DB and cache
                creds = await get_quickbooks_credentials(tenant_id, db)
                if creds:
                    self._quickbooks_creds_cache[tenant_id] = creds
                    if tenant_id not in self._creds_cache_timestamps:
                        self._creds_cache_timestamps[tenant_id] = {}
                    self._creds_cache_timestamps[tenant_id]["quickbooks"] = (
                        datetime.now(UTC)
                    )
                    print(f"💾 Cached QuickBooks credentials for tenant {tenant_id}")
            if not creds:
                print(
                    f"ℹ️  Tenant {tenant_id} has no QuickBooks credentials - no port 8002 access"
                )
                return None

            current_token = creds["access_token"]

            # STEP 2: Check if token changed (refreshed)
            cached_token = self._tenant_tokens.get(tenant_id)
            if cached_token and cached_token != current_token:
                print(
                    f"🔄 QuickBooks token refreshed for tenant {tenant_id} - invalidating cache"
                )
                # Invalidate cached MCP (has old token)
                await self._invalidate_connection(tenant_id, "quickbooks")

            # STEP 3: Check if connection is stale (too old)
            if self._is_connection_stale(tenant_id, "quickbooks"):
                print(
                    f"⏰ QuickBooks connection is stale for tenant {tenant_id} - will recreate"
                )
                await self._invalidate_connection(tenant_id, "quickbooks")

            # STEP 4: Check cache - REUSE if exists and valid
            if tenant_id in self._tenant_connections:
                if "quickbooks" in self._tenant_connections[tenant_id]:
                    print(
                        f"♻️  Reusing cached QuickBooks MCP (port 8002) for tenant {tenant_id}"
                    )
                    return self._tenant_connections[tenant_id]["quickbooks"]

            # STEP 4.5: Check failed connections cache - skip if recently failed (with TTL)
            if not self._is_failure_expired(tenant_id, "quickbooks"):
                print(
                    f"⚡ Skipping QuickBooks MCP (port 8002) - recently failed for tenant {tenant_id}"
                )
                return None

            # STEP 5: Create new MCP connection to port 8002
            await self._ensure_exit_stack()
            assert self._exit_stack is not None, "Exit stack must be initialized"

            try:
                mcp_params = MCPServerStreamableHttpParams(
                    url=settings.accounts_mcp_server,  # Hosted or local MCP
                    headers={
                        "jsonrpc": "2.0",
                        "Content-Type": "application/json, text/event-stream",
                        "Authorization": f"Bearer {creds['access_token']}",
                        "x-quickbooks-realm-id": creds["realm_id"],
                    },
                    timeout=8,  # OPTIMIZED: Reduced from 15s - fail fast for connection issues
                    sse_read_timeout=60 * 5,
                )

                # Wrap MCP creation in a timeout to prevent hanging
                try:
                    # BUGFIX: Filter out problematic tools with invalid schemas
                    # OpenAI rejects tools with array params that don't define 'items'
                    tool_filter = create_static_tool_filter(
                        blocked_tool_names=[
                            "search_employees"
                        ]  # Invalid schema: array missing items
                    )

                    mcp_server = await asyncio.wait_for(
                        self._exit_stack.enter_async_context(
                            MCPServerStreamableHttp(
                                params=mcp_params,
                                name=f"QB_MCP_{tenant_id}",
                                # tool_filter=tool_filter,
                                cache_tools_list=True,
                                client_session_timeout_seconds=60,  # Increased for image generation (was 15s)
                                max_retry_attempts=1,  # OPTIMIZED: Reduced from 2 - fail faster
                                retry_backoff_seconds_base=1.0,  # OPTIMIZED: Reduced from 2.0s
                            )
                        ),
                        timeout=10.0,  # OPTIMIZED: Reduced from 20s - fail fast
                    )
                except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                    print(
                        f"⚠️  QuickBooks MCP connection {type(e).__name__} for tenant {tenant_id}"
                    )
                    print(f"   URL: {settings.accounts_mcp_server}")
                    print(f"   Accounts agent will work without QuickBooks tools")
                    # Cache the failure with TTL to avoid retrying too frequently
                    self._mark_connection_failed(tenant_id, "quickbooks")
                    return None
                except Exception as e:
                    # Catch any other exception during MCP creation
                    print(
                        f"⚠️  QuickBooks MCP creation failed: {type(e).__name__}: {str(e)}"
                    )
                    print(f"   URL: {settings.accounts_mcp_server}")
                    print(f"   Accounts agent will work without QuickBooks tools")
                    # Cache the failure with TTL to avoid retrying too frequently
                    self._mark_connection_failed(tenant_id, "quickbooks")
                    return None

                # CACHE the connection for reuse (reduces latency)
                if tenant_id not in self._tenant_connections:
                    self._tenant_connections[tenant_id] = {}
                self._tenant_connections[tenant_id]["quickbooks"] = mcp_server
                self._tenant_tokens[tenant_id] = (
                    current_token  # Track token for change detection
                )

                # Track creation time for staleness detection
                if tenant_id not in self._connection_created_at:
                    self._connection_created_at[tenant_id] = {}
                self._connection_created_at[tenant_id]["quickbooks"] = datetime.now(UTC)

                print(f"✅ Created QuickBooks MCP for tenant {tenant_id}")
                print(f"   URL: {settings.accounts_mcp_server}")
                return mcp_server

            except Exception as e:
                # Outer catch-all for any other errors
                print(
                    f"⚠️  Failed to create QuickBooks MCP: {type(e).__name__}: {str(e)[:100]}"
                )
                print(f"   Accounts agent will work without QuickBooks tools")
                # Cache the failure with TTL to avoid retrying too frequently
                self._mark_connection_failed(tenant_id, "quickbooks")
                return None

    # ========================================================================
    # Global MCP (Port 8001) - For Sales, Marketing, Inventory, Payment, Analytics
    # ========================================================================

    async def get_global_mcp(
        self,
        tenant_id: UUID,
        db: AsyncSession,
    ) -> Optional[MCPServerStreamableHttp]:
        """
        Get Global MCP server for a tenant (Port 8001).

        Used by: Sales, Marketing, Inventory, Payment, Analytics agents.
        NOT used by: Main/Triage agent (no tools) or Accounts agent (uses port 8002).

        This dynamically passes credentials for services the tenant has connected:
        - Google Sheets (refresh token, inventory/orders workbook IDs and worksheet names)
        - Stripe, Shopify, etc. (TODO: when you add those tables)

        CONCURRENCY FIX: Uses request-scoped cache so multiple agents (marketing, inventory)
        in the same request share the same connection instead of creating duplicates.

        Returns:
            MCP server with service credentials in headers, or None if no services connected
        """
        # STEP 0: Check request-scoped cache FIRST (no lock needed - contextvars are thread-safe)
        # This allows multiple agents in the same request to share the same connection
        request_cache = _request_global_mcp.get()
        if tenant_id in request_cache:
            print(
                f"♻️  Reusing request-scoped Global MCP (port 8001) for tenant {tenant_id}"
            )
            return request_cache[tenant_id]

        lock = await self._get_tenant_lock(tenant_id)

        async with lock:
            # Double-check after acquiring lock (another coroutine might have created it)
            request_cache = _request_global_mcp.get()
            if tenant_id in request_cache:
                print(
                    f"♻️  Reusing request-scoped Global MCP (port 8001) for tenant {tenant_id} (after lock)"
                )
                return request_cache[tenant_id]

            # STEP 1: Get Google Sheets credentials from database
            sheets_creds = await self._get_google_sheets_credentials(tenant_id, db)

            # STEP 2: Check if token changed (would happen after refresh on MCP side)
            # For now, we always pass refresh_token and let MCP handle refresh
            # In future, you could track access_token changes like QuickBooks

            # STEP 3: Check failed connections cache - skip if recently failed (with TTL)
            if not self._is_failure_expired(tenant_id, "global"):
                print(
                    f"⚡ Skipping Global MCP (port 8001) - recently failed for tenant {tenant_id}"
                )
                return None

            # STEP 4: Create fresh connection for this request
            print(f"🔄 Creating fresh Global MCP (port 8001) for tenant {tenant_id}")

            # STEP 5: Build headers with dynamic credentials
            headers = {
                "jsonrpc": "2.0",
                "Content-Type": "application/json, text/event-stream",
                "x-tenant-id": str(
                    tenant_id
                ),  # Pass tenant_id for multi-tenant isolation
            }

            # Add Google Sheets credentials if available
            if sheets_creds:
                headers["x-user-refresh-token"] = sheets_creds["refresh_token"]
                if sheets_creds.get("inventory_workbook_id"):
                    headers["x-inventory-workbook-id"] = sheets_creds[
                        "inventory_workbook_id"
                    ]
                if sheets_creds.get("inventory_worksheet_name"):
                    headers["x-inventory-worksheet-name"] = sheets_creds[
                        "inventory_worksheet_name"
                    ]
                if sheets_creds.get("orders_workbook_id"):
                    headers["x-orders-workbook-id"] = sheets_creds["orders_workbook_id"]
                if sheets_creds.get("orders_worksheet_name"):
                    headers["x-orders-worksheet-name"] = sheets_creds[
                        "orders_worksheet_name"
                    ]
                print(
                    f"✅ Added Google Sheets credentials to headers for tenant {tenant_id}"
                )
            else:
                print(f"ℹ️  Tenant {tenant_id} has no Google Sheets credentials")

            print(f"✅ Added tenant_id to headers: {tenant_id}")

            # TODO: Add other service credentials here when you have those tables
            # if stripe_creds:
            #     headers["x-stripe-api-key"] = stripe_creds["api_key"]
            # if shopify_creds:
            #     headers["x-shopify-access-token"] = shopify_creds["access_token"]

            # STEP 6: Create new MCP connection
            await self._ensure_exit_stack()
            assert self._exit_stack is not None, "Exit stack must be initialized"

            try:
                # TODO: Add service-based filtering when service tables exist
                # tool_filter = await self._create_tool_filter(tenant_id, db)

                mcp_params = MCPServerStreamableHttpParams(
                    url=settings.global_mcp_server,  # Port 8001 - Global server (uses env var)
                    headers=headers,
                    timeout=5,  # Shorter timeout for faster failure
                    sse_read_timeout=60 * 5,
                )

                # Wrap MCP creation in a timeout to prevent hanging
                try:
                    mcp_server = await asyncio.wait_for(
                        self._exit_stack.enter_async_context(
                            MCPServerStreamableHttp(
                                params=mcp_params,
                                name=f"Global_Port8001_{tenant_id}",
                                # tool_filter=tool_filter,  # TODO: Add when service tables exist
                                cache_tools_list=True,
                                client_session_timeout_seconds=100,  # Increased for image generation (was 10s)
                                max_retry_attempts=0,  # No retries - fail fast
                                retry_backoff_seconds_base=1.0,
                            )
                        ),
                        timeout=3.0,  # 3 second total timeout for faster failure
                    )
                except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                    print(
                        f"⚠️  Global MCP (port 8001) connection {type(e).__name__} for tenant {tenant_id}"
                    )
                    print(f"   Agents will work without global MCP tools")
                    # Cache the failure with TTL to avoid retrying too frequently
                    self._mark_connection_failed(tenant_id, "global")
                    return None
                except Exception as e:
                    # Catch any other exception during MCP creation
                    print(
                        f"⚠️  Global MCP (port 8001) creation failed: {type(e).__name__}"
                    )
                    print(f"   Agents will work without global MCP tools")
                    # Cache the failure with TTL to avoid retrying too frequently
                    self._mark_connection_failed(tenant_id, "global")
                    return None

                # Cache in request-scoped context so other agents in same request can reuse
                request_cache = _request_global_mcp.get()
                if not request_cache:
                    request_cache = {}
                    _request_global_mcp.set(request_cache)
                request_cache[tenant_id] = mcp_server

                print(f"✅ Created fresh Global MCP (port 8001) for tenant {tenant_id}")
                return mcp_server

            except Exception as e:
                # Outer catch-all for any other errors
                print(
                    f"⚠️  Failed to create Global MCP: {type(e).__name__}: {str(e)[:100]}"
                )
                print(f"   Agents will work without global MCP tools")
                # Cache the failure with TTL to avoid retrying too frequently
                self._mark_connection_failed(tenant_id, "global")
                return None

    # ========================================================================
    # Helper: Get ALL MCP servers for a tenant
    # ========================================================================

    # ========================================================================
    # Helper Methods - Don't call directly, use specific get_* methods above
    # ========================================================================

    async def _get_google_sheets_credentials(
        self, tenant_id: UUID, db: AsyncSession
    ) -> Optional[dict]:
        """
        Get Google Sheets credentials from database with caching.

        Returns:
            Dict with keys:
            - refresh_token: str
            - inventory_workbook_id: Optional[str]
            - inventory_worksheet_name: Optional[str]
            - orders_workbook_id: Optional[str]
            - orders_worksheet_name: Optional[str]
            Or None if tenant has no Google Sheets connection.
        """
        # PERFORMANCE: Check cache first to avoid DB query
        if tenant_id in self._sheets_creds_cache and not self._is_creds_cache_stale(
            tenant_id, "sheets"
        ):
            print(f"⚡ Using cached Google Sheets credentials for tenant {tenant_id}")
            return self._sheets_creds_cache[tenant_id]

        from app.models.google_sheets_connection import GoogleSheetsConnection

        stmt = select(GoogleSheetsConnection).where(
            GoogleSheetsConnection.tenant_id == tenant_id,
            GoogleSheetsConnection.is_active == True,
        )
        result = await db.execute(stmt)
        connection = result.scalar_one_or_none()

        if not connection:
            # Cache the None result too (avoid repeated DB queries)
            self._sheets_creds_cache[tenant_id] = None
            if tenant_id not in self._creds_cache_timestamps:
                self._creds_cache_timestamps[tenant_id] = {}
            self._creds_cache_timestamps[tenant_id]["sheets"] = datetime.now(UTC)
            return None

        # Check if token is expired
        if connection.token_expires_at <= datetime.now():
            print(f"⚠️  Google Sheets token expired for tenant {tenant_id}")
            # MCP server will handle refresh using refresh_token
            # We still pass the refresh_token so MCP can get a new access_token

        creds = {
            "refresh_token": connection.refresh_token,
            "inventory_workbook_id": connection.inventory_workbook_id,
            "inventory_worksheet_name": connection.inventory_worksheet_name,
            "orders_workbook_id": connection.orders_workbook_id,
            "orders_worksheet_name": connection.orders_worksheet_name,
        }

        # Cache the credentials
        self._sheets_creds_cache[tenant_id] = creds
        if tenant_id not in self._creds_cache_timestamps:
            self._creds_cache_timestamps[tenant_id] = {}
        self._creds_cache_timestamps[tenant_id]["sheets"] = datetime.now(UTC)
        print(f"💾 Cached Google Sheets credentials for tenant {tenant_id}")

        return creds

    async def _get_connected_services(
        self, tenant_id: UUID, db: AsyncSession
    ) -> List[str]:
        """
        Check which services tenant has connected (Stripe, Shopify, etc.).

        TODO: Implement when you create service connection tables.

        Returns:
            List of connected service names (e.g., ["stripe", "shopify"])
        """
        # Placeholder - implement when you have service tables
        # For now, return empty list
        return []

    # ========================================================================
    # Cleanup
    # ========================================================================

    async def invalidate_tenant(self, tenant_id: UUID):
        """Remove all cached connections for a tenant."""
        # FIX: Use tenant-specific lock instead of global lock to avoid blocking other tenants
        lock = await self._get_tenant_lock(tenant_id)
        async with lock:
            if tenant_id in self._tenant_connections:
                del self._tenant_connections[tenant_id]
            if tenant_id in self._tenant_tokens:
                del self._tenant_tokens[tenant_id]
            if tenant_id in self._connection_created_at:
                del self._connection_created_at[tenant_id]
            if tenant_id in self._failed_connections:
                del self._failed_connections[tenant_id]
            # Also clear credential caches
            if tenant_id in self._quickbooks_creds_cache:
                del self._quickbooks_creds_cache[tenant_id]
            if tenant_id in self._sheets_creds_cache:
                del self._sheets_creds_cache[tenant_id]
            if tenant_id in self._creds_cache_timestamps:
                del self._creds_cache_timestamps[tenant_id]
            print(
                f"🔄 Invalidated all MCP connections and caches for tenant {tenant_id}"
            )

    async def handle_connection_error(
        self, tenant_id: UUID, connection_type: str, error: Exception
    ):
        """
        Handle MCP connection errors (like ClosedResourceError).

        Invalidates the broken connection so it gets recreated on next request.
        This provides automatic recovery from connection failures.

        Args:
            tenant_id: Tenant whose connection failed
            connection_type: "quickbooks" or "global"
            error: The exception that occurred
        """
        from anyio import ClosedResourceError

        if isinstance(error, ClosedResourceError):
            print(
                f"⚠️  MCP connection closed for tenant {tenant_id} ({connection_type})"
            )
            print(f"   Will recreate connection on next request")
            await self._invalidate_connection(tenant_id, connection_type)
        else:
            print(
                f"⚠️  MCP connection error for tenant {tenant_id} ({connection_type}): {type(error).__name__}"
            )
            # Invalidate connection for other errors too, to be safe
            await self._invalidate_connection(tenant_id, connection_type)

    async def cleanup(self):
        """Cleanup all connections. Call on app shutdown."""
        print("🔌 Cleaning up unified MCP manager...")

        try:
            if self._exit_stack:
                await self._exit_stack.__aexit__(None, None, None)
                print("✅ All MCP connections closed")
        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")
        finally:
            self._tenant_connections.clear()
            self._tenant_tokens.clear()
            self._locks.clear()
            self._exit_stack = None


def clear_request_mcp_cache():
    """
    Clear the request-scoped MCP connection cache.

    Call this at the end of each request to ensure connections are properly
    cleaned up and not leaked between requests.

    Note: The connections themselves are managed by the AsyncExitStack,
    this just clears the request-scoped references.
    """
    try:
        _request_global_mcp.set({})
    except Exception:
        pass  # Ignore errors if context is not set


# Global instance
unified_mcp_manager = UnifiedMCPManager()
