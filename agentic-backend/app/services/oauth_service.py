"""
OAuth authentication service using Authlib
Handles Google OAuth2 login flow for Tenants
"""

from typing import Optional, Dict, Any
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status

from app.core.config import settings
from app.models.tenant import Tenant
from app.schema.oauth import OAuthUserInfo
from app.services.auth_service import AuthService

# Load OAuth configuration
config = Config(".env")
oauth = OAuth(config)

# Register Google OAuth provider
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


class OAuthService:
    """Service for OAuth authentication operations - works with Tenant"""

    @staticmethod
    def get_oauth_client(provider: str = "google"):
        """Get OAuth client for specified provider"""
        if provider == "google":
            return oauth.google
        raise ValueError(f"Unsupported OAuth provider: {provider}")

    @staticmethod
    async def handle_google_callback(
        code: str, db: AsyncSession, redirect_uri: Optional[str] = None
    ) -> tuple[Tenant, Any]:
        """
        Handle Google OAuth callback and return tenant with tokens.
        Uses Authlib's built-in token exchange for reliability.

        Args:
            code: Authorization code from Google
            db: Database session
            redirect_uri: Optional redirect URI (must match the one used in authorization)

        Returns:
            Tuple of (Tenant, TokenResponse)
        """
        try:
            import httpx

            # Exchange code for tokens manually - more reliable than Authlib in async context
            if not redirect_uri:
                redirect_uri = settings.google_redirect_uri

            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }

            async with httpx.AsyncClient() as client:
                token_response = await client.post(token_url, data=token_data)
                token_response.raise_for_status()
                tokens = token_response.json()

                # Get user info
                userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
                headers = {"Authorization": f"Bearer {tokens['access_token']}"}
                userinfo_response = await client.get(userinfo_url, headers=headers)
                userinfo_response.raise_for_status()
                user_info = userinfo_response.json()

            # Create OAuth user info
            oauth_info = OAuthUserInfo(
                provider="google",
                provider_id=user_info["id"],  # Google's unique user ID
                email=user_info["email"],
                name=user_info.get("name"),
                avatar_url=user_info.get("picture"),
                is_email_verified=user_info.get("verified_email", True),
            )

            # Get or create tenant
            tenant = await OAuthService.get_or_create_oauth_tenant(oauth_info, db)

            # Refresh to ensure all attributes are loaded before returning
            await db.refresh(tenant)

            # Capture values while still in async context
            tenant_id = str(tenant.id)
            tenant_email = tenant.email

            print(f"✅ Tenant found/created: {tenant_id}, email: {tenant_email}")

            # Generate JWT tokens
            print(f"🔵 Generating tokens for tenant: {tenant_id}")
            tokens = await AuthService._generate_tokens(tenant, db)
            print(f"✅ Tokens generated successfully")

            return tenant, tokens

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth authentication failed: {str(e)}",
            )

    @staticmethod
    async def get_or_create_oauth_tenant(
        oauth_info: OAuthUserInfo, db: AsyncSession
    ) -> Tenant:
        """
        Get existing tenant by OAuth ID or create new tenant from OAuth data.
        If tenant exists by email but not OAuth, link the OAuth account.
        """
        # First, check if tenant exists with this OAuth provider ID
        statement = select(Tenant).where(
            Tenant.oauth_provider == oauth_info.provider,
            Tenant.oauth_id == oauth_info.provider_id,
        )
        result = await db.exec(statement)
        tenant = result.first()

        if tenant:
            # Tenant exists with this OAuth account
            # Update avatar if changed
            if oauth_info.avatar_url and tenant.avatar_url != oauth_info.avatar_url:
                tenant.avatar_url = oauth_info.avatar_url
                db.add(tenant)
                await db.commit()
                await db.refresh(tenant)
            return tenant

        # Check if tenant exists by email (might have registered with password before)
        statement = select(Tenant).where(Tenant.email == oauth_info.email)
        result = await db.exec(statement)
        existing_tenant = result.first()

        if existing_tenant:
            # Tenant exists with email but no OAuth linked
            # Link this OAuth account to existing tenant
            existing_tenant.oauth_provider = oauth_info.provider
            existing_tenant.oauth_id = oauth_info.provider_id
            existing_tenant.is_oauth_user = True
            existing_tenant.is_email_verified = True  # OAuth emails are verified

            if oauth_info.avatar_url:
                existing_tenant.avatar_url = oauth_info.avatar_url
            if oauth_info.name and not existing_tenant.name:
                existing_tenant.name = oauth_info.name

            db.add(existing_tenant)
            await db.commit()
            await db.refresh(existing_tenant)
            return existing_tenant

        # Create new tenant from OAuth data
        # Generate unique slug
        import re

        email_domain = oauth_info.email.split("@")[0]
        base_slug = re.sub(r"[^a-z0-9-]", "", email_domain.lower())
        slug = base_slug

        counter = 1
        while True:
            statement = select(Tenant).where(Tenant.slug == slug)
            result = await db.exec(statement)
            if not result.first():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1

        new_tenant = Tenant(
            email=oauth_info.email,
            name=oauth_info.name,
            avatar_url=oauth_info.avatar_url,
            is_email_verified=True,  # OAuth emails are pre-verified
            oauth_provider=oauth_info.provider,
            oauth_id=oauth_info.provider_id,
            is_oauth_user=True,
            password_hash=None,  # OAuth-only tenant, no password
            slug=slug,
            role="admin",
            is_active=True,
            subscription_plan="free",
        )

        db.add(new_tenant)
        await db.commit()
        await db.refresh(new_tenant)

        return new_tenant
