"""
Google Sheets OAuth schemas
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class GoogleSheetsAuthURL(BaseModel):
    """Response model for Google Sheets authorization URL"""

    auth_url: str = Field(description="Google OAuth authorization URL")


class SheetConfig(BaseModel):
    """Configuration for a single sheet (inventory or orders)"""

    workbook_id: str = Field(description="Google Sheets spreadsheet ID")
    worksheet_name: str = Field(description="Name of the worksheet/tab")


class GoogleSheetsConfig(BaseModel):
    """Complete Google Sheets configuration"""

    inventory: Optional[SheetConfig] = Field(
        default=None, description="Inventory sheet configuration"
    )
    orders: Optional[SheetConfig] = Field(
        default=None, description="Orders sheet configuration"
    )


class SaveSheetsConfigRequest(BaseModel):
    """Request to save Google Sheets configuration"""

    inventory: SheetConfig = Field(description="Inventory sheet configuration")
    orders: SheetConfig = Field(description="Orders sheet configuration")


class GoogleSheetsConnectionStatus(BaseModel):
    """Google Sheets connection status response"""

    is_connected: bool = Field(description="Whether Google Sheets is connected")
    refresh_token: Optional[str] = Field(
        default=None, description="OAuth refresh token"
    )
    token_expires_at: Optional[datetime] = Field(
        default=None, description="Token expiration timestamp"
    )
    is_token_expired: bool = Field(
        default=False, description="Whether the token is expired"
    )
    inventory_workbook_id: Optional[str] = Field(
        default=None, description="Inventory spreadsheet ID"
    )
    inventory_worksheet_name: Optional[str] = Field(
        default=None, description="Inventory worksheet name"
    )
    orders_workbook_id: Optional[str] = Field(
        default=None, description="Orders spreadsheet ID"
    )
    orders_worksheet_name: Optional[str] = Field(
        default=None, description="Orders worksheet name"
    )
    last_synced_at: Optional[datetime] = Field(
        default=None, description="Last sync timestamp"
    )


class SpreadsheetInfo(BaseModel):
    """Information about a Google Spreadsheet"""

    id: str = Field(description="Spreadsheet ID")
    name: str = Field(description="Spreadsheet name")


class WorksheetInfo(BaseModel):
    """Information about a worksheet/tab in a spreadsheet"""

    name: str = Field(description="Worksheet name")
    index: int = Field(description="Worksheet index/position")
    row_count: int = Field(description="Number of rows")
    column_count: int = Field(description="Number of columns")


class SpreadsheetsListResponse(BaseModel):
    """Response containing list of spreadsheets"""

    spreadsheets: list[SpreadsheetInfo] = Field(
        description="List of available spreadsheets"
    )


class WorksheetsListResponse(BaseModel):
    """Response containing list of worksheets in a spreadsheet"""

    worksheets: list[WorksheetInfo] = Field(
        description="List of worksheets in the spreadsheet"
    )


class GoogleSheetsDisconnectResponse(BaseModel):
    """Response after disconnecting Google Sheets"""

    message: str = Field(description="Success message")
    disconnected: bool = Field(description="Whether disconnection was successful")


class OrderItem(BaseModel):
    """Individual order item from Orders sheet"""

    id: str = Field(description="Order ID")
    date: str = Field(description="Order date")
    customer: str = Field(description="Customer name")
    amount: float = Field(description="Order amount as number")
    amount_display: str = Field(description="Order amount with currency formatting")
    method: str = Field(description="Payment method")
    status: str = Field(description="Order status (completed/pending/failed)")


class OrdersStats(BaseModel):
    """Statistics calculated from orders data"""

    total_revenue: float = Field(description="Total revenue from completed orders")
    completed_count: int = Field(description="Number of completed orders")
    pending_count: int = Field(description="Number of pending orders")


class OrdersDataResponse(BaseModel):
    """Response containing orders data from Google Sheets"""

    orders: list[OrderItem] = Field(description="List of orders")
    stats: OrdersStats = Field(description="Calculated statistics")
    last_synced_at: str = Field(description="Last sync timestamp")
