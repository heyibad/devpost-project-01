from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status

from app.models.tenant import Tenant
from app.models.refresh_token import RefreshToken
from app.core.security import hash_password, verify_password, hash_token
from app.utils.jwt import create_access_token, create_refresh_token, decode_token
from app.schema.auth import UserRegister, UserLogin, TokenResponse
from app.core.config import settings


class AuthService:
    """Service for authentication operations - works with Tenant (primary entity)"""

    @staticmethod
    async def register_tenant(
        tenant_data: UserRegister, db: AsyncSession
    ) -> tuple[Tenant, TokenResponse]:
        """Register a new tenant (primary user account)"""
        # Check if tenant exists
        statement = select(Tenant).where(Tenant.email == tenant_data.email)
        result = await db.exec(statement)
        existing_tenant = result.first()

        if existing_tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Generate slug from email
        import re

        email_domain = tenant_data.email.split("@")[0]
        base_slug = re.sub(r"[^a-z0-9-]", "", email_domain.lower())
        slug = base_slug

        # Ensure slug is unique
        counter = 1
        while True:
            statement = select(Tenant).where(Tenant.slug == slug)
            result = await db.exec(statement)
            if not result.first():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Create tenant
        hashed_password = hash_password(tenant_data.password)
        new_tenant = Tenant(
            email=tenant_data.email,
            password_hash=hashed_password,
            name=tenant_data.name,
            is_email_verified=False,
            slug=slug,
            role="admin",
            is_active=True,
            subscription_plan="free",
        )

        db.add(new_tenant)
        await db.commit()
        await db.refresh(new_tenant)

        # Detach tenant from session to prevent lazy loading issues
        db.expunge(new_tenant)

        # Generate tokens (need to get tenant back in session)
        statement = select(Tenant).where(Tenant.id == new_tenant.id)
        result = await db.exec(statement)
        tenant_for_tokens = result.first()
        if tenant_for_tokens:
            tokens = await AuthService._generate_tokens(tenant_for_tokens, db)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate tokens",
            )

        return new_tenant, tokens

    @staticmethod
    async def login_tenant(
        login_data: UserLogin, db: AsyncSession
    ) -> tuple[Tenant, TokenResponse]:
        """Login tenant and return tokens"""
        # Get tenant by email
        statement = select(Tenant).where(Tenant.email == login_data.email)
        result = await db.exec(statement)
        tenant = result.first()

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Verify password
        if not tenant.password_hash or not verify_password(
            login_data.password, tenant.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Generate tokens
        tokens = await AuthService._generate_tokens(tenant, db)

        return tenant, tokens

    @staticmethod
    async def refresh_access_token(
        refresh_token: str, db: AsyncSession
    ) -> TokenResponse:
        """Refresh access token using refresh token"""
        try:
            # Decode refresh token
            payload = decode_token(refresh_token)

            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )

            tenant_id = payload.get("sub")
            if not tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                )

            # Check if token is in database and not revoked
            token_hash = hash_token(refresh_token)
            statement = select(RefreshToken).where(
                RefreshToken.token_hash == token_hash, RefreshToken.revoked == False
            )
            result = await db.exec(statement)
            token_record = result.first()

            if not token_record:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token not found or revoked",
                )

            # Check if token expired
            from datetime import timezone

            current_time = datetime.now(timezone.utc).replace(tzinfo=None)
            token_expires = (
                token_record.expires_at.replace(tzinfo=None)
                if token_record.expires_at.tzinfo
                else token_record.expires_at
            )
            if token_expires < current_time:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
                )

            # Get tenant
            tenant = await db.get(Tenant, UUID(tenant_id))
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant not found"
                )

            # Generate new tokens
            new_tokens = await AuthService._generate_tokens(tenant, db)

            # Revoke old refresh token
            token_record.revoked = True
            db.add(token_record)
            await db.commit()

            return new_tokens

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    @staticmethod
    async def logout_tenant(refresh_token: str, db: AsyncSession) -> dict:
        """Logout tenant by revoking refresh token"""
        token_hash = hash_token(refresh_token)
        statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await db.exec(statement)
        token_record = result.first()

        if token_record:
            token_record.revoked = True
            db.add(token_record)
            await db.commit()

        return {"message": "Successfully logged out"}

    @staticmethod
    async def get_tenant_by_email(email: str, db: AsyncSession) -> Optional[Tenant]:
        """Get tenant by email"""
        statement = select(Tenant).where(Tenant.email == email)
        result = await db.exec(statement)
        return result.first()

    @staticmethod
    async def _generate_tokens(tenant: Tenant, db: AsyncSession) -> TokenResponse:
        """Generate access and refresh tokens for tenant"""
        # Create access token with tenant information
        access_token = create_access_token(
            data={
                "sub": str(tenant.id),
                "email": tenant.email,
                "tenant_id": str(
                    tenant.id
                ),  # tenant_id is same as sub for primary tenant
            }
        )

        # Create refresh token with tenant information
        refresh_token = create_refresh_token(
            data={"sub": str(tenant.id), "tenant_id": str(tenant.id)}
        )

        # Store refresh token in database
        token_hash = hash_token(refresh_token)
        expires_at = datetime.utcnow() + timedelta(
            days=settings.refresh_token_expire_days
        )

        refresh_token_record = RefreshToken(
            tenant_id=tenant.id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False,
        )

        db.add(refresh_token_record)
        await db.commit()

        # Return tokens
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    @staticmethod
    async def add_password(
        tenant: Tenant, new_password: str, confirm_password: str, db: AsyncSession
    ) -> dict:
        """Add password for OAuth users who don't have one"""
        # Check if user already has a password
        if tenant.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password already exists. Use change password instead.",
            )

        # Verify passwords match
        if new_password != confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match",
            )

        # Hash and save the new password
        hashed_password = hash_password(new_password)

        # Get fresh tenant from database
        statement = select(Tenant).where(Tenant.id == tenant.id)
        result = await db.exec(statement)
        db_tenant = result.first()

        if not db_tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        db_tenant.password_hash = hashed_password
        db.add(db_tenant)
        await db.commit()

        return {"message": "Password added successfully"}

    @staticmethod
    async def change_password(
        tenant: Tenant, old_password: str, new_password: str, db: AsyncSession
    ) -> dict:
        """Change password for users who already have one"""
        # Get fresh tenant from database
        statement = select(Tenant).where(Tenant.id == tenant.id)
        result = await db.exec(statement)
        db_tenant = result.first()

        if not db_tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        # Check if user has a password to change
        if not db_tenant.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No password set. Use add password instead.",
            )

        # Verify old password
        if not verify_password(old_password, db_tenant.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )

        # Hash and save the new password
        hashed_password = hash_password(new_password)
        db_tenant.password_hash = hashed_password
        db.add(db_tenant)
        await db.commit()

        return {"message": "Password changed successfully"}

    @staticmethod
    async def get_password_status(tenant: Tenant, db: AsyncSession) -> dict:
        """Get password status for a tenant"""
        # Get fresh tenant from database to ensure we have latest data
        statement = select(Tenant).where(Tenant.id == tenant.id)
        result = await db.exec(statement)
        db_tenant = result.first()

        if not db_tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found",
            )

        return {
            "has_password": db_tenant.password_hash is not None,
            "is_oauth_user": db_tenant.is_oauth_user,
            "oauth_provider": db_tenant.oauth_provider,
        }
