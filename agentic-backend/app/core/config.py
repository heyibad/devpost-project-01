import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

from sqlmodel import Field


class Settings(BaseSettings):
    # App Settings
    app_name: str = "FastAPI Agentic Backend"
    version: str = "0.1.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    # Database - PostgreSQL
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    # JWT
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production", alias="JWT_SECRET"
    )
    algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # Google OAuth
    google_client_id: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(
        default=None, alias="GOOGLE_CLIENT_SECRET"
    )
    google_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/oauth/google/callback",
        alias="GOOGLE_REDIRECT_URI",
    )

    # QuickBooks OAuth
    quickbooks_client_id: Optional[str] = Field(
        default=None, alias="QUICKBOOKS_CLIENT_ID"
    )
    quickbooks_client_secret: Optional[str] = Field(
        default=None, alias="QUICKBOOKS_CLIENT_SECRET"
    )
    quickbooks_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/quickbooks/callback",
        alias="QUICKBOOKS_REDIRECT_URI",
    )
    quickbooks_scopes: str = Field(
        default="com.intuit.quickbooks.accounting",
        alias="QUICKBOOKS_SCOPES",
    )
    quickbooks_use_sandbox: bool = Field(default=True, alias="QUICKBOOKS_USE_SANDBOX")

    # Google Sheets OAuth
    google_sheets_client_id: Optional[str] = Field(
        default=None, alias="GOOGLE_SHEETS_CLIENT_ID"
    )
    google_sheets_client_secret: Optional[str] = Field(
        default=None, alias="GOOGLE_SHEETS_CLIENT_SECRET"
    )
    google_sheets_redirect_uri: str = Field(
        default="https://sahulat-backend-d8a8fd5d5e2f.herokuapp.com/api/v1/oauth/google/callback",
        alias="GOOGLE_SHEETS_REDIRECT_URI",
    )
    google_sheets_scopes: str = Field(
        default="https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.readonly",
        alias="GOOGLE_SHEETS_SCOPES",
    )

    # AI AGENT CONFIGURATION
    api_key: str = Field(default="", alias="API_KEY")
    api_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai/",
        alias="API_BASE_URL",
    )
    model: str = Field(default="gemini-2.5-flash", alias="MODEL")
    OPENAI_API_KEY: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")

    # Evolution (WhatsApp) API
    evolution_api_url: Optional[str] = Field(default=None, alias="EVOLUTION_API_URL")
    evolution_api_key: Optional[str] = Field(default=None, alias="EVOLUTION_API_KEY")
    webhook_url: Optional[str] = Field(default=None, alias="WEBHOOK_URL")

    # MCP SERVER CONFIGURATION
    mcp_server_urls: str = Field(
        default="https://sahulat-ai-566875055155.us-east4.run.app/mcp",
        alias="MCP_SERVER_URLS",
    )  # Comma-separated URLs

    # Accounts-specific MCP server URL (for QuickBooks with dynamic credentials)
    # Hosted on Heroku or can run locally
    # Prioritize environment variable over .env file
    accounts_mcp_server: str = Field(
        default_factory=lambda: os.getenv(
            "ACCOUNTS_MCP_SERVER_URL", "http://host.docker.internal:8002/mcp"
        ),
        alias="ACCOUNTS_MCP_SERVER_URL",
    )

    # Global MCP server URL (for Sales, Marketing, Inventory, Payment, Analytics)
    # Local: http://mcp:8001/mcp (Docker service name)
    # Production: Use the GCP Cloud Run URL
    global_mcp_server: str = Field(
        default_factory=lambda: os.getenv(
            "GLOBAL_MCP_SERVER_URL", "http://mcp:8001/mcp"
        ),
        alias="GLOBAL_MCP_SERVER_URL",
    )

    @property
    def mcp_servers_list(self) -> list[str]:
        """Parse MCP server URLs from comma-separated string"""
        if not self.mcp_server_urls:
            return []
        return [url.strip() for url in self.mcp_server_urls.split(",") if url.strip()]

    # CORS
    allowed_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000", alias="ALLOWED_ORIGINS"
    )

    # Frontend URL for OAuth redirects
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")

    # Resend Email Service
    resend_api_key: Optional[str] = Field(default=None, alias="RESEND_API_KEY")
    email_from_address: str = Field(
        default="Sahulat AI <contact@sahulatai.app>", alias="EMAIL_FROM_ADDRESS"
    )

    # Datadog LLM Observability Configuration
    dd_api_key: Optional[str] = Field(default=None, alias="DD_API_KEY")
    dd_site: str = Field(default="us5.datadoghq.com", alias="DD_SITE")
    dd_llmobs_enabled: bool = Field(default=False, alias="DD_LLMOBS_ENABLED")
    dd_llmobs_ml_app: str = Field(default="sahulat-ai", alias="DD_LLMOBS_ML_APP")
    dd_service: str = Field(default="agentic-backend", alias="DD_SERVICE")
    dd_env: str = Field(default="dev", alias="DD_ENV")

    @property
    def cors_origins(self) -> list[str]:
        """Parse allowed origins from comma-separated string"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()
