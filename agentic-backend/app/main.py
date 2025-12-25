from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from app.api.v1 import api_router
from app.core.config import settings
import traceback
import logging
import warnings
import sys


# Suppress specific warnings and errors
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*cancel scope.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Configure logging to suppress noisy errors that don't affect functionality
logging.getLogger("sqlalchemy.pool").setLevel(logging.CRITICAL)  # Changed to CRITICAL
logging.getLogger("sqlalchemy.engine").setLevel(logging.CRITICAL)
logging.getLogger("anyio").setLevel(logging.CRITICAL)
logging.getLogger("httpcore").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)

# Custom exception hook to suppress SQLAlchemy connection errors
original_excepthook = sys.excepthook


def custom_excepthook(exc_type, exc_value, exc_traceback):
    """Suppress specific exceptions from being printed to stderr"""
    # Suppress CancelledError from SQLAlchemy connection cleanup
    if exc_type.__name__ == "CancelledError":
        if "cancel scope" in str(exc_value):
            return  # Silently ignore

    # Suppress "Exception terminating connection" errors
    if "Exception terminating connection" in str(exc_value):
        return  # Silently ignore

    # For other exceptions, use original handler
    original_excepthook(exc_type, exc_value, exc_traceback)


sys.excepthook = custom_excepthook


# Import unified MCP manager (single source of truth)
from app.services.unified_mcp_manager import unified_mcp_manager

# Import Datadog tracing integration
from app.core.datadog_tracing import init_datadog_tracing, flush_traces, is_llmobs_enabled


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Handles startup and shutdown events for the application.
    """
    # STARTUP
    print("\n🚀 Starting Agentic Backend API...")
    
    # Initialize Datadog LLM Observability
    llmobs_enabled = init_datadog_tracing()
    if llmobs_enabled:
        print("✅ Datadog LLM Observability enabled")
    else:
        print("ℹ️  Datadog LLM Observability not configured (set DD_API_KEY and DD_LLMOBS_ENABLED=1)")
    
    print("✅ Unified MCP Manager ready (connections created on-demand)")
    print("   - Port 8002: QuickBooks (Accounts agent only)")
    print("   - Port 8001: Global services (Sales, Marketing, etc.)")

    # Suppress asyncio task exception logging for known MCP cleanup errors
    import asyncio

    loop = asyncio.get_event_loop()

    def custom_exception_handler(loop, context):
        """Custom exception handler to suppress known MCP cleanup errors"""
        exception = context.get("exception")
        message = context.get("message", "")

        # Suppress known MCP library cleanup errors
        if exception:
            error_type = type(exception).__name__
            if error_type in ("RuntimeError", "CancelledError", "GeneratorExit"):
                if "cancel scope" in str(exception) or "cancel scope" in message:
                    return  # Silently ignore

        # Suppress "ASGI callable" errors
        if "ASGI callable" in message or "ASGI" in str(exception):
            return  # Silently ignore

        # Suppress connection termination errors
        if "Exception terminating connection" in message:
            return  # Silently ignore

        # For other exceptions, use default handler
        loop.default_exception_handler(context)

    loop.set_exception_handler(custom_exception_handler)

    # Monkey-patch uvicorn logger to suppress "ASGI callable" error
    uvicorn_logger = logging.getLogger("uvicorn.error")
    original_error = uvicorn_logger.error

    def filtered_error(msg, *args, **kwargs):
        """Filter out ASGI callable errors"""
        if "ASGI callable" not in str(msg):
            original_error(msg, *args, **kwargs)

    uvicorn_logger.error = filtered_error

    yield

    # SHUTDOWN: Cleanup all resources
    print("\n🛑 Shutting down Agentic Backend API...")
    
    # Flush any pending Datadog traces
    if is_llmobs_enabled():
        flush_traces()
        print("✅ Datadog traces flushed")
    
    await unified_mcp_manager.cleanup()


app = FastAPI(
    title="Agentic Backend API",
    description="AI Agent/Chatbot backend with authentication, conversation management, and message streaming.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Add global exception handler for better error messages
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    error_detail = {
        "error": type(exc).__name__,
        "message": str(exc),
        "path": str(request.url),
    }
    # Print without unicode characters for Windows console compatibility
    print(f"ERROR - Unhandled exception: {error_detail}")
    traceback.print_exc()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=error_detail
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )


# Add session middleware (required for OAuth state management)
app.add_middleware(
    SessionMiddleware, secret_key=settings.secret_key, max_age=3600  # 1 hour
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "Agentic Backend API is running!",
        "status": "healthy",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
