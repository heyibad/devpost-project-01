from fastapi import APIRouter
from app.api.v1 import (
    auth,
    oauth,
    quickbooks,
    google_sheets,
    posters,
    whatsapp,
    webhook_router,
    waitlist,
    admin,
)
from app.api.v1 import chat

api_router = APIRouter(prefix="/api/v1")

# Include routers
api_router.include_router(auth.router)
api_router.include_router(oauth.router)
api_router.include_router(quickbooks.router)
api_router.include_router(google_sheets.router)
api_router.include_router(chat.router)
api_router.include_router(posters.router)
api_router.include_router(whatsapp.router)
api_router.include_router(webhook_router.router)
api_router.include_router(waitlist.router)
api_router.include_router(admin.router)

__all__ = ["api_router"]
