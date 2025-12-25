"""
Datadog LLM Observability Integration for OpenAI Agents SDK.

This module provides integration between Datadog's LLM Observability
and the OpenAI Agents SDK, enabling comprehensive tracing of:
- Agent workflows and handoffs
- LLM generations and responses
- Tool/function calls
- Guardrails and custom spans

The Datadog integration automatically converts OpenAI Agents SDK tracing
into Datadog's LLM Observability format when enabled.

Usage:
    # During app startup
    from app.core.datadog_tracing import init_datadog_tracing
    init_datadog_tracing()

    # In your agent code - traces are automatically captured
    result = await Runner.run(agent, prompt)

    # For custom workflow spans
    from app.core.datadog_tracing import llmobs_workflow
    with llmobs_workflow("my-workflow"):
        result = await Runner.run(agent, prompt)

Environment Variables Required:
    - DD_API_KEY: Your Datadog API key
    - DD_LLMOBS_ENABLED: Set to "true" or "1" to enable (default: false)
    - DD_LLMOBS_ML_APP: Name of your ML application (default: sahulat-ai)
    - DD_SERVICE: Service name for APM (default: agentic-backend)
    - DD_ENV: Environment name (default: development)
"""

import os
import logging
from typing import Optional, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Global state for LLMObs
_llmobs_enabled = False
_llmobs_instance = None


def init_datadog_tracing() -> bool:
    """
    Initialize Datadog LLM Observability and APM tracing.

    This function sets up:
    1. ddtrace auto-instrumentation for OpenAI and other libraries
    2. LLM Observability for capturing agent spans

    The OpenAI Agents SDK integration automatically converts:
    - traces → LLM workflow spans
    - agent → agent spans
    - generation → LLM call spans
    - response → response spans
    - guardrail → guardrail spans
    - handoff → handoff spans
    - function → tool spans
    - custom → custom spans

    Returns:
        bool: True if LLM Observability was successfully enabled
    """
    global _llmobs_enabled, _llmobs_instance

    from app.core.config import settings

    # Check if DD API key is available
    if not settings.dd_api_key:
        logger.info("Datadog API key not configured - LLM Observability disabled")
        return False

    # Set environment variables for ddtrace
    os.environ.setdefault("DD_API_KEY", settings.dd_api_key)
    os.environ.setdefault("DD_SITE", settings.dd_site)
    os.environ.setdefault("DD_SERVICE", settings.dd_service)
    os.environ.setdefault("DD_ENV", settings.dd_env)

    # Enable LLM Observability via environment variable
    if settings.dd_llmobs_enabled:
        os.environ["DD_LLMOBS_ENABLED"] = "1"
        os.environ["DD_LLMOBS_ML_APP"] = settings.dd_llmobs_ml_app

    try:
        # Import ddtrace components
        from ddtrace import patch_all, tracer
        from ddtrace.llmobs import LLMObs

        # Patch all supported libraries (includes openai)
        # This enables automatic tracing for HTTP clients, databases, etc.
        patch_all()

        # For agentless mode on Windows, we don't need to configure the tracer
        # as LLMObs will send directly to Datadog

        if settings.dd_llmobs_enabled:
            # Initialize LLM Observability in agentless mode
            # This sends traces directly to Datadog without needing the DD Agent
            LLMObs.enable(
                ml_app=settings.dd_llmobs_ml_app,
                api_key=settings.dd_api_key,
                site=settings.dd_site,  # Use the DD_SITE (e.g., us5.datadoghq.com)
                agentless_enabled=True,  # Send directly to Datadog without agent
            )

            _llmobs_instance = LLMObs
            _llmobs_enabled = True

            logger.info(
                f"✅ Datadog LLM Observability enabled for app: {settings.dd_llmobs_ml_app}"
            )
            logger.info(f"   Site: {settings.dd_site} (agentless mode)")

            return True
        else:
            logger.info("Datadog APM tracing enabled (LLM Observability disabled)")
            return False

    except ImportError as e:
        logger.warning(f"ddtrace not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Datadog tracing: {e}")
        return False


def is_llmobs_enabled() -> bool:
    """Check if LLM Observability is enabled."""
    return _llmobs_enabled


def get_llmobs():
    """Get the LLMObs instance if enabled."""
    return _llmobs_instance


@contextmanager
def llmobs_workflow(
    name: str,
    session_id: Optional[str] = None,
    ml_app: Optional[str] = None,
):
    """
    Context manager for wrapping agent workflows in LLM Observability spans.

    This creates a top-level workflow span that groups all nested agent
    operations, making it easier to visualize complete conversation flows.

    Args:
        name: Name of the workflow (e.g., "chat-completion", "user-query")
        session_id: Optional session/conversation ID for grouping
        ml_app: Optional ML app name override

    Yields:
        The workflow span if LLMObs is enabled, None otherwise

    Example:
        with llmobs_workflow("handle-chat", session_id=conversation_id):
            result = await Runner.run(agent, user_message)
    """
    if not _llmobs_enabled or _llmobs_instance is None:
        yield None
        return

    try:
        with _llmobs_instance.workflow(
            name=name, session_id=session_id, ml_app=ml_app
        ) as span:
            yield span
    except Exception as e:
        logger.warning(f"LLMObs workflow span error: {e}")
        yield None


@contextmanager
def llmobs_task(name: str, session_id: Optional[str] = None):
    """
    Context manager for task-level spans within a workflow.

    Use this for sub-operations within a workflow that aren't
    direct LLM calls but are still worth tracking.

    Args:
        name: Name of the task
        session_id: Optional session ID

    Example:
        with llmobs_task("retrieve-context"):
            context = await fetch_documents(query)
    """
    if not _llmobs_enabled or _llmobs_instance is None:
        yield None
        return

    try:
        with _llmobs_instance.task(name=name, session_id=session_id) as span:
            yield span
    except Exception as e:
        logger.warning(f"LLMObs task span error: {e}")
        yield None


def annotate_span(
    input_data: Optional[Any] = None,
    output_data: Optional[Any] = None,
    metadata: Optional[dict] = None,
    tags: Optional[dict] = None,
    span: Optional[Any] = None,
):
    """
    Annotate the current or specified span with additional data.

    Args:
        input_data: Input data to the operation
        output_data: Output data from the operation
        metadata: Additional metadata dict
        tags: Custom tags dict
        span: Specific span to annotate (uses current if None)
    """
    if not _llmobs_enabled or _llmobs_instance is None:
        return

    try:
        _llmobs_instance.annotate(
            span=span,
            input_data=input_data,
            output_data=output_data,
            metadata=metadata,
            tags=tags,
        )
    except Exception as e:
        logger.warning(f"LLMObs annotation error: {e}")


def export_span_context() -> Optional[dict]:
    """
    Export the current span context for distributed tracing.

    Returns:
        dict with span_id and trace_id, or None if not available
    """
    if not _llmobs_enabled or _llmobs_instance is None:
        return None

    try:
        return _llmobs_instance.export_span()
    except Exception as e:
        logger.warning(f"Failed to export span context: {e}")
        return None


def flush_traces():
    """
    Flush any pending traces to Datadog.

    Call this during shutdown to ensure all traces are sent.
    """
    if not _llmobs_enabled or _llmobs_instance is None:
        return

    try:
        _llmobs_instance.flush()
        logger.info("LLM Observability traces flushed")
    except Exception as e:
        logger.warning(f"Failed to flush traces: {e}")


def disable_tracing():
    """
    Disable LLM Observability (useful for testing).
    """
    global _llmobs_enabled

    if _llmobs_instance is not None:
        try:
            _llmobs_instance.disable()
        except Exception:
            pass

    _llmobs_enabled = False
    logger.info("LLM Observability disabled")
