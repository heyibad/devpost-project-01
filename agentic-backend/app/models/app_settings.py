"""
Global application settings model.
Stores system-wide configuration like waitlist toggle.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class AppSettings(SQLModel, table=True):
    """
    Global application settings.
    Single row table for storing system-wide configuration.
    """

    __tablename__ = "app_settings"

    id: int = Field(default=1, primary_key=True, nullable=False)

    # Waitlist settings
    waitlist_enabled: bool = Field(default=True, nullable=False)

    # Timestamps
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_by: Optional[str] = Field(
        default=None, nullable=True
    )  # Admin email who last updated
