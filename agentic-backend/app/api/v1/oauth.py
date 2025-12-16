"""
OAuth authentication endpoints
Handles Google OAuth2 login flow
"""

from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.utils.db import get_db
from app.schema.oauth import GoogleAuthURL, GoogleCallback
from app.schema.auth import TokenResponse
from app.schema.user import UserResponse
from app.services.oauth_service import OAuthService, oauth
from app.core.config import settings

router = APIRouter(prefix="/oauth", tags=["OAuth Authentication"])


@router.get("/google/login")
async def google_login(request: Request):
    """
    Initiate Google OAuth login flow.

    Redirects user to Google's authorization page.
    After user authorizes, Google will redirect back to /oauth/google/callback
    """
    from urllib.parse import urlencode

    # Use the configured redirect URI from settings
    redirect_uri = settings.google_redirect_uri

    # Build Google OAuth URL manually to avoid state issues
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(
    code: str, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    Google OAuth callback endpoint.

    Google redirects here after user authorizes the application.
    This endpoint exchanges the authorization code for user info and creates/logs in the user.
    """
    try:
        print(f"🔵 OAuth Callback - Received code: {code[:20]}...")

        # Use the service method to handle the callback (more reliable)
        # Logging happens inside the service method
        tenant, tokens = await OAuthService.handle_google_callback(code=code, db=db)

        # Redirect to frontend with tokens
        frontend_url = settings.frontend_url

        print(f"🔵 Redirecting to: {frontend_url}/auth/callback")
        # Redirect to frontend with tokens in URL params
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?access_token={tokens.access_token}&refresh_token={tokens.refresh_token}"
        )

    except Exception as e:
        print(f"❌ OAuth Error: {str(e)}")
        import traceback

        traceback.print_exc()
        # Redirect to frontend with error
        frontend_url = settings.frontend_url
        import urllib.parse

        error_message = urllib.parse.quote(str(e))
        return RedirectResponse(
            url=f"{frontend_url}/auth/callback?error={error_message}"
        )


@router.post("/google/token", response_model=TokenResponse)
async def google_token_exchange(
    callback_data: GoogleCallback, db: AsyncSession = Depends(get_db)
):
    """
    Exchange Google authorization code for JWT tokens (for mobile/SPA apps).

    This endpoint is for applications that handle OAuth flow themselves
    and just need to exchange the authorization code for JWT tokens.
    """
    tenant, tokens = await OAuthService.handle_google_callback(
        code=callback_data.code, db=db
    )

    return tokens


@router.get("/google/auth-url", response_model=GoogleAuthURL)
async def get_google_auth_url(request: Request):
    """
    Get Google OAuth authorization URL (for mobile/SPA apps).

    Returns the URL that the client should redirect to for Google OAuth login.
    After authorization, Google will redirect to the configured redirect_uri.
    """
    from authlib.integrations.starlette_client import OAuthError

    try:
        google = oauth.google

        # Build the authorization URL
        redirect_uri = settings.google_redirect_uri

        # Use Authlib's method to create authorization URL
        # For async context, we need to properly handle the OAuth client
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={settings.google_client_id}&redirect_uri={redirect_uri}&response_type=code&scope=openid%20email%20profile&access_type=offline"

        return GoogleAuthURL(auth_url=auth_url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate auth URL: {str(e)}",
        )
