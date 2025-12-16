from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID


class TenantRegister(BaseModel):
    """Schema for tenant registration"""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    name: Optional[str] = None


class TenantLogin(BaseModel):
    """Schema for tenant login"""

    email: EmailStr
    password: str


# Backward compatibility
UserRegister = TenantRegister
UserLogin = TenantLogin


class TokenResponse(BaseModel):
    """Schema for token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Schema for token refresh"""

    refresh_token: str


class TokenData(BaseModel):
    """Schema for token data payload"""

    tenant_id: Optional[UUID] = None
    email: Optional[str] = None

    # Backward compatibility
    @property
    def user_id(self):
        return self.tenant_id


class PasswordReset(BaseModel):
    """Schema for password reset"""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""

    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class ChangePassword(BaseModel):
    """Schema for password change (requires current password)"""

    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class AddPassword(BaseModel):
    """Schema for OAuth users to add a password"""

    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)


class PasswordStatus(BaseModel):
    """Schema for password status response"""

    has_password: bool
    is_oauth_user: bool
    oauth_provider: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    """Schema for Google OAuth"""

    code: str
    redirect_uri: str
