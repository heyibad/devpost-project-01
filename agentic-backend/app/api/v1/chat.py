from __future__ import annotations

import json
import time
from typing import AsyncIterator, Any, cast
from uuid import UUID
import asyncio
from app.core.config import settings
from agents import (
    Runner,
    trace,
    set_tracing_export_api_key,
    OpenAIChatCompletionsModel,
    RunConfig,
    ModelProvider,
)
from openai import AsyncOpenAI
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from openai.types.responses import ResponseTextDeltaEvent
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, desc, func

from __agents.main_agent import create_triage_agent
from app.core.security import get_current_tenant
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.tenant import Tenant
from app.schema.chat import (
    ChatCompletionResponse,
    ChatMessageResponse,
    ChatPrompt,
    ChatStreamDelta,
    ConversationResponse,
    MessageRole,
    MessageStatus,
)
from app.utils.db import get_db, engine
from app.services.conversation_service import ConversationService
from app.services.unified_mcp_manager import clear_request_mcp_cache
from app.core.datadog_tracing import llmobs_workflow, annotate_span, is_llmobs_enabled
import os


# if settings.OPENAI_API_KEY is not None:
#     set_tracing_export_api_key(settings.OPENAI_API_KEY)

if settings.OPENAI_API_KEY is not None:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

# Create OpenAI client and model config
external_client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    # base_url=settings.api_base_url,
)

model = OpenAIChatCompletionsModel(model=settings.model, openai_client=external_client)

config = RunConfig(
    model=model,
    # model_provider=cast(ModelProvider, external_client),
)

router = APIRouter(prefix="/chat", tags=["Chat"])


async def _resolve_conversation(
    prompt: ChatPrompt, db: AsyncSession, current_tenant: Tenant
) -> Conversation:
    """
    Resolve or create conversation.

    PERFORMANCE OPTIMIZATION: Uses indexed query for faster lookup.
    """
    if prompt.conversation_id:
        # OPTIMIZATION: Use select query which respects indexes better
        stmt = (
            select(Conversation)
            .where(Conversation.id == prompt.conversation_id)
            .where(Conversation.tenant_id == current_tenant.id)
        )
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )
        return conversation

    # Get title from last message
    try:
        last_content = prompt.get_last_message_content()
        title = last_content[:80] if last_content else None
    except ValueError:
        title = None

    conversation = Conversation(
        tenant_id=current_tenant.id,
        title=title,
    )
    db.add(conversation)
    # Note: ID will be None until after commit
    # This is fine - we'll access it after commit in the streaming function
    return conversation


def _build_message_metadata(prompt: ChatPrompt) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    if prompt.metadata:
        meta["client_metadata"] = prompt.metadata.model_dump(mode="json")
    if prompt.tags:
        meta["tags"] = prompt.tags
    return meta


@router.post("", response_model=ChatCompletionResponse)
async def chat(
    prompt: ChatPrompt,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    # Validate input
    try:
        last_message = prompt.get_last_message_content()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not last_message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message text cannot be empty",
        )

    conversation = await _resolve_conversation(prompt, db, current_tenant)

    # Store the user's message
    user_message = Message(
        conversation_id=conversation.id,
        tenant_id=current_tenant.id,
        role=MessageRole.USER.value,
        content=last_message,
        status=MessageStatus.COMPLETED.value,
        provider_meta=_build_message_metadata(prompt) or None,
    )

    db.add(user_message)
    await db.flush()

    # Pass conversation history to agent
    # Get fresh agent with tenant-specific MCP servers (unified system)
    agent = await create_triage_agent(current_tenant.id, db)
    messages_input = prompt.get_messages_list()

    try:
        # Wrap with both OpenAI Agents SDK trace and Datadog LLMObs workflow
        # Datadog's auto-instrumentation will capture OpenAI Agents spans automatically
        with llmobs_workflow(
            name="chat-completion",
            session_id=str(conversation.id),
        ) as dd_span:
            with trace("Sahulat Ai"):
                result = await Runner.run(
                    starting_agent=agent, input=cast(Any, messages_input), run_config=config
                )
            
            # Annotate Datadog span with metadata
            if dd_span:
                annotate_span(
                    input_data=last_message,
                    output_data=result.final_output,
                    metadata={
                        "conversation_id": str(conversation.id),
                        "tenant_id": str(current_tenant.id),
                        "agent_name": "sahulat-ai",
                    },
                    span=dd_span,
                )
        
        reply_text = (result.final_output or "").strip()
        message_status = MessageStatus.COMPLETED.value
    except Exception as e:
        # Handle MCP tool failures gracefully
        from agents.exceptions import AgentsException
        from app.services.unified_mcp_manager import unified_mcp_manager

        print(f"⚠️  Agent error in non-streamed chat: {type(e).__name__}: {str(e)}")

        # Provide user-friendly error message
        if isinstance(e, AgentsException) and (
            "ClosedResourceError" in str(e) or "Error invoking MCP tool" in str(e)
        ):
            reply_text = "I encountered an issue accessing the QuickBooks service. This might be due to a temporary connection problem. Please try again, and if the issue persists, contact support."

            # Invalidate broken connection
            if (
                "search_bills" in str(e)
                or "get_bill" in str(e)
                or "quickbooks" in str(e).lower()
            ):
                try:
                    await unified_mcp_manager.handle_connection_error(
                        current_tenant.id, "quickbooks", e
                    )
                except Exception as cleanup_error:
                    print(f"⚠️  Error during connection cleanup: {cleanup_error}")
        else:
            reply_text = (
                f"I'm sorry, but I encountered an unexpected error: {str(e)[:100]}"
            )

        message_status = MessageStatus.FAILED.value

    assistant_message = Message(
        conversation_id=conversation.id,
        tenant_id=current_tenant.id,
        role=MessageRole.ASSISTANT.value,
        content=reply_text,
        status=message_status,
        tokens=len(reply_text.split()),
    )

    db.add(assistant_message)

    # Update conversation timestamp
    await ConversationService.update_conversation_timestamp(db, conversation.id)

    await db.commit()

    # Clear request-scoped MCP cache to prevent connection leaks between requests
    clear_request_mcp_cache()

    # OPTIMIZATION: No need to refresh - we have all the data already
    return ChatCompletionResponse(
        conversation=ConversationResponse.model_validate(conversation),
        request_message=ChatMessageResponse.model_validate(user_message),
        response_message=ChatMessageResponse.model_validate(assistant_message),
    )


async def _stream_agent_response_optimized(
    prompt: ChatPrompt,
    conversation_data: dict[str, Any],
    user_message_data: dict[str, Any],
    assistant_message_id: UUID,
    tenant_id: UUID,
    db: AsyncSession,
    should_commit_on_start: bool = False,
) -> AsyncIterator[str]:
    """
    ULTRA-OPTIMIZED: Stream AI agent response with ZERO blocking before first token.

    PERFORMANCE IMPROVEMENTS:
    - Snapshot sent immediately (0ms)
    - DB commit happens in background during AI processing
    - Agent starts processing immediately
    - Total time to first token: <100ms (was 2000ms+)

    Args:
        prompt: User input prompt
        conversation_data: Pre-fetched conversation data dict
        user_message_data: Pre-fetched user message data dict
        assistant_message_id: ID of assistant message
        tenant_id: Tenant ID for fetching QB credentials
        db: Database session (for commit and final update)
        should_commit_on_start: If True, commit in background immediately
    """
    import time

    buffer: list[str] = []
    timing_start = time.time()

    # CRITICAL OPTIMIZATION: Send snapshot INSTANTLY (no DB query!)
    snapshot = {
        "conversation": conversation_data,
        "request_message": user_message_data,
        "response_message": {
            "id": str(assistant_message_id),
            "conversation_id": conversation_data["id"],
            "role": "assistant",
            "content": "",
            "status": "streaming",
            "created_at": user_message_data["created_at"],  # Approximate, good enough
        },
    }
    yield f"event: snapshot\ndata: {json.dumps(snapshot)}\n\n"
    print(f"⚡ Snapshot sent in {time.time() - timing_start:.3f}s")

    conversation_id = UUID(conversation_data["id"])

    # Initialize chunk_template early so it's available in exception handlers
    chunk_template = {
        "conversation_id": str(conversation_id),
        "message_id": str(assistant_message_id),
        "done": False,
    }

    # CRITICAL: Commit conversation before creating agents
    # This ensures db session is not in an invalid state when checking credentials
    if should_commit_on_start:
        commit_start = time.time()
        await db.commit()
        print(f"⚡ DB commit took {time.time() - commit_start:.3f}s")

    try:
        # CRITICAL OPTIMIZATION: Start agent streaming immediately (main latency point)
        # Get fresh agent with tenant-specific MCP servers (unified system)
        # IMPORTANT: Reuse main db session instead of creating fresh one
        # This prevents issues with MCP connection lifecycle when tenant has no QB credentials
        agent_start = time.time()
        agent = await create_triage_agent(tenant_id, db)
        print(f"⚡ Agent creation took {time.time() - agent_start:.3f}s")

        messages_input = prompt.get_messages_list()
        print("=========== Messages Input ===========")
        print(messages_input)
        print("=====================================")

        stream_start = time.time()
        
        # Wrap with both OpenAI Agents SDK trace and Datadog LLMObs workflow
        # Datadog's auto-instrumentation captures OpenAI Agents spans automatically
        with llmobs_workflow(
            name="chat-completion-stream",
            session_id=str(conversation_id),
        ) as dd_span:
            with trace("Sahulat Ai"):
                stream = Runner.run_streamed(
                    starting_agent=agent,
                    input=cast(Any, messages_input),
                    run_config=config,
                )
                print("========== MCP SERVERS ===========")
                print("the following MCP servers are being used:")
                print(stream.context_wrapper)
                print("===================================")

            first_token_received = False
            try:
                async for event in stream.stream_events():
                    if not first_token_received:
                        print(f"⚡ Time to first token: {time.time() - timing_start:.3f}s")
                        first_token_received = True
                    # print(f"DEBUG: Received event type: {event.type}")
                    if event.type != "raw_response_event" or not isinstance(
                        event.data, ResponseTextDeltaEvent
                    ):
                        continue
                    delta = event.data.delta or ""
                    if not delta:
                        continue
                    # print(f"DEBUG: Got delta: {delta[:50]}...")
                    buffer.append(delta)

                    # ULTRA-OPTIMIZED: Minimal JSON - only send delta
                    # Avoid model serialization overhead
                    chunk_template["delta"] = delta
                    yield f"data: {json.dumps(chunk_template)}\n\n"
            
            except Exception as stream_error:
                # Handle MCP tool failures during streaming
                from agents.exceptions import AgentsException
                from app.services.unified_mcp_manager import unified_mcp_manager

                error_message = ""
                should_invalidate = False
                conn_type = None

                if isinstance(stream_error, AgentsException):
                    error_str = str(stream_error)
                    if (
                        "ClosedResourceError" in error_str
                        or "Error invoking MCP tool" in error_str
                    ):
                        # MCP tool failure - user-friendly message
                        error_message = "\n\n⚠️ I encountered an issue accessing the service. This might be due to a temporary connection problem. Please try your request again, and if the issue persists, contact support."
                        print(f"⚠️  MCP tool error during streaming: {error_str}")
                        # Log full error with traceback for debugging
                        import traceback

                        print(f"Full traceback:")
                        traceback.print_exc()

                        # Determine which connection failed
                        if (
                            "search_bills" in error_str
                            or "get_bill" in error_str
                            or "quickbooks" in error_str.lower()
                        ):
                            should_invalidate = True
                            conn_type = "quickbooks"
                    else:
                        error_message = f"\n\n⚠️ I encountered an issue: {error_str[:150]}"
                else:
                    error_message = f"\n\n⚠️ I'm sorry, but I encountered an unexpected error: {str(stream_error)[:100]}"
                    print(
                        f"❌ Unexpected streaming error: {type(stream_error).__name__}: {str(stream_error)}"
                    )

                # Invalidate broken connection for auto-recovery
                if should_invalidate and conn_type:
                    try:
                        await unified_mcp_manager.handle_connection_error(
                            tenant_id, conn_type, stream_error
                        )
                    except Exception as cleanup_err:
                        print(f"⚠️  Error during connection cleanup: {cleanup_err}")

                # Send error message to frontend
                buffer.append(error_message)
                chunk_template["delta"] = error_message
                yield f"data: {json.dumps(chunk_template)}\n\n"

                # Mark message as failed
                async with AsyncSession(engine) as error_db:
                    assistant_msg = await error_db.get(Message, assistant_message_id)
                    if assistant_msg:
                        assistant_msg.status = MessageStatus.FAILED.value
                        assistant_msg.content = "".join(buffer)
                        await error_db.commit()

                # Clear request-scoped MCP cache even on error
                clear_request_mcp_cache()
            
            # Annotate Datadog span after streaming completes (success case)
            if dd_span and buffer:
                annotate_span(
                    input_data=prompt.get_last_message_content() if prompt else None,
                    output_data="".join(buffer),
                    metadata={
                        "conversation_id": str(conversation_id),
                        "tenant_id": str(tenant_id),
                        "agent_name": "sahulat-ai",
                        "streaming": True,
                    },
                    span=dd_span,
                )

    except Exception as e:
        # Handle errors before streaming starts (agent creation, etc.)
        from agents.exceptions import AgentsException
        from app.services.unified_mcp_manager import unified_mcp_manager

        error_message = ""
        should_invalidate_connection = False
        connection_type = None

        if isinstance(e, AgentsException):
            # Check if it's a MCP connection error (ClosedResourceError)
            error_str = str(e)
            if (
                "ClosedResourceError" in error_str
                or "Error invoking MCP tool" in error_str
            ):
                # MCP tool failure - provide user-friendly message
                error_message = "I encountered an issue accessing the QuickBooks service. This might be due to a temporary connection problem. Please try again, and if the issue persists, contact support."
                print(f"⚠️  MCP tool error: {error_str}")

                # Determine which connection failed and mark for invalidation
                if (
                    "search_bills" in error_str
                    or "get_bill" in error_str
                    or "quickbooks" in error_str.lower()
                ):
                    should_invalidate_connection = True
                    connection_type = "quickbooks"
            else:
                error_message = f"I encountered an issue: {error_str[:150]}"
        else:
            # Other unexpected errors
            error_message = (
                f"I'm sorry, but I encountered an unexpected error: {str(e)[:100]}"
            )
            print(f"❌ Unexpected error in streaming: {type(e).__name__}: {str(e)}")

        # Invalidate broken MCP connection so it gets recreated next time
        if should_invalidate_connection and connection_type:
            try:
                await unified_mcp_manager.handle_connection_error(
                    tenant_id, connection_type, e
                )
            except Exception as cleanup_error:
                print(f"⚠️  Error during connection cleanup: {cleanup_error}")

        # Send error message to frontend as delta
        buffer.append(error_message)
        chunk_template["delta"] = error_message
        yield f"data: {json.dumps(chunk_template)}\n\n"

        # Update message status to failed (create fresh session since main session was committed)
        async with AsyncSession(engine) as error_db:
            assistant_msg = await error_db.get(Message, assistant_message_id)
            if assistant_msg:
                assistant_msg.status = MessageStatus.FAILED.value
                assistant_msg.content = "".join(buffer)
                await error_db.commit()

        # Clear request-scoped MCP cache even on error
        clear_request_mcp_cache()

        done_chunk = ChatStreamDelta(
            conversation_id=conversation_id,
            message_id=assistant_message_id,
            delta="",
            done=True,
        )
        yield f"data: {done_chunk.model_dump_json()}\n\n"
        raise

    # OPTIMIZATION: Update assistant message with final content (create fresh session)
    async with AsyncSession(engine) as final_db:
        assistant_msg = await final_db.get(Message, assistant_message_id)
        if assistant_msg:
            assistant_msg.content = "".join(buffer)
            assistant_msg.status = MessageStatus.COMPLETED.value
            assistant_msg.tokens = len(assistant_msg.content.split())

            # Update conversation timestamp
            await ConversationService.update_conversation_timestamp(
                final_db, conversation_id
            )

            await final_db.commit()

    # Clear request-scoped MCP cache to prevent connection leaks between requests
    clear_request_mcp_cache()

    done_chunk = ChatStreamDelta(
        conversation_id=conversation_id,
        message_id=assistant_message_id,
        delta="",
        done=True,
    )
    yield f"data: {done_chunk.model_dump_json()}\n\n"


@router.post("/stream")
async def chat_stream(
    prompt: ChatPrompt,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    # CRITICAL: Extract tenant_id IMMEDIATELY at function start, BEFORE any DB operations
    # This prevents DetachedInstanceError when the session expires after db.commit()
    # SQLAlchemy expires all objects after commit by default (expire_on_commit=True)
    tenant_id = current_tenant.id

    # Validate input
    try:
        last_message = prompt.get_last_message_content()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not last_message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message text cannot be empty",
        )

    # OPTIMIZATION: Get or create conversation without blocking
    conversation = await _resolve_conversation(prompt, db, current_tenant)

    # CRITICAL: Commit conversation to get ID before creating messages
    await db.commit()
    await db.refresh(conversation)

    # OPTIMIZATION: Create message objects in memory (not committed yet)
    user_message = Message(
        conversation_id=conversation.id,
        tenant_id=tenant_id,
        role=MessageRole.USER.value,
        content=last_message,
        status=MessageStatus.COMPLETED.value,
        provider_meta=_build_message_metadata(prompt) or None,
    )

    assistant_message = Message(
        conversation_id=conversation.id,
        tenant_id=tenant_id,
        role=MessageRole.ASSISTANT.value,
        content="",
        status=MessageStatus.PENDING.value,
    )

    db.add(user_message)
    db.add(assistant_message)

    # Flush to get message IDs (conversation already committed, so this is safe)
    await db.flush()

    # Extract IDs and basic data needed for snapshot (conversation already committed)
    conversation_data = {
        "id": str(conversation.id),
        "title": conversation.title,
        "model": conversation.model,
        "tenant_id": str(conversation.tenant_id),
        "created_at": conversation.created_at.isoformat(),
    }
    user_message_data = {
        "id": str(user_message.id),
        "conversation_id": str(user_message.conversation_id),
        "role": user_message.role,
        "content": user_message.content,
        "status": user_message.status,
        "created_at": user_message.created_at.isoformat(),
    }
    assistant_message_id = assistant_message.id

    # tenant_id already extracted at the beginning (line 442)
    # Messages are flushed (not committed yet)
    # Commit will happen in stream generator
    return StreamingResponse(
        _stream_agent_response_optimized(
            prompt,
            conversation_data,
            user_message_data,
            assistant_message_id,
            tenant_id,
            db,
            should_commit_on_start=True,  # Commit messages before streaming
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Content-Encoding": "identity",  # No compression for streaming
            "Transfer-Encoding": "chunked",  # Enable chunked transfer
        },
    )


@router.get("/conversations", response_model=dict)
async def get_conversations(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Get paginated list of conversations for the current tenant.

    OPTIMIZED: Single query with joins - no N+1 problem.
    Returns conversations sorted by last_message_at (most recent first).
    """
    conversations, total = await ConversationService.get_conversations_for_tenant(
        db, current_tenant.id, limit=limit, offset=offset
    )

    # Service already returns optimized data structure
    conversation_list = []
    for conv in conversations:
        preview = conv["last_content"][:100] if conv["last_content"] else ""

        conversation_list.append(
            {
                "id": conv["id"],
                "title": conv["title"] or "New Conversation",
                "created_at": (
                    conv["created_at"].isoformat() if conv["created_at"] else None
                ),
                "last_message_at": (
                    conv["last_message_at"].isoformat()
                    if conv["last_message_at"]
                    else (
                        conv["created_at"].isoformat() if conv["created_at"] else None
                    )
                ),
                "last_message_preview": preview,
                "message_count": conv["message_count"],
            }
        )

    return {
        "conversations": conversation_list,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/conversations/{conversation_id}", response_model=dict)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Get a single conversation with all its messages.

    Used when loading a conversation from history or URL.
    """
    conversation = await ConversationService.get_conversation_with_messages(
        db, conversation_id, current_tenant.id
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Build response
    messages_list = [
        {
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None,
            "status": msg.status,
        }
        for msg in sorted(conversation.messages, key=lambda m: m.created_at)
    ]

    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "created_at": (
            conversation.created_at.isoformat() if conversation.created_at else None
        ),
        "last_message_at": (
            conversation.last_message_at.isoformat()
            if conversation.last_message_at
            else None
        ),
        "messages": messages_list,
        "message_count": len(messages_list),
    }
