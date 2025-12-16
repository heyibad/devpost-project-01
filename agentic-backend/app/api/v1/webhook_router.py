import os
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
import json
import httpx
import asyncio
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.utils.db import get_db
from app.core.config import settings

# Services & models from your app
from app.services.user_service import get_user_by_phone, create_user
from app.models.user import User
from app.models.user_messages import UserMessage
from app.models.whatsapp_cred import WhatsAppCred

# Import the sales agent
from __agents.sales import create_sales_agent
from agents import Runner, trace

if settings.OPENAI_API_KEY is not None:
    os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

router = APIRouter(prefix="/webhook_router", tags=["Webhook"])

# Evolution API configuration from environment variables
EVOLUTION_API_BASE_URL = settings.evolution_api_url
EVOLUTION_API_KEY = settings.evolution_api_key

async def generate_agent_reply(user_message: str, history: list[dict], tenant_id: UUID, phone_number: str, db: AsyncSession) -> str:
    """
    Generate agent reply using the sales agent with conversation history.
    history: list of dicts with role/content for context.
    phone_number: Customer's phone number for WhatsApp messaging.
    """
    try:
        # Create the sales agent with phone_number
        sales_agent = await create_sales_agent(tenant_id=tenant_id, db=db, phone_number=phone_number)
        
        # Format the conversation history
        conversation_history = "\n".join([
            f"{msg['role']}: {msg['content']}" for msg in history
        ])
        
        # Create the prompt with history
        prompt = f"""Conversation History:
{conversation_history} \n

Current User Message: {user_message}
"""
        with trace("Sales Agent"):
        # Run the agent with the prompt
         result = await Runner.run(sales_agent,prompt)
        
        # Extract the response text from the result
        if hasattr(result, 'data'):
            return str(result.data)
        else:
            return str(result.final_output)
            
    except Exception as e:
        # Fallback to a simple response if agent fails
        print(f"Agent error: {str(e)}")
        return f"Thank you for your message. How can I assist you today?"


async def send_whatsapp_media(instance_id: str, phone_number: str, media_url: str, caption: str) -> tuple[Optional[int], Optional[str]]:
    """
    Send WhatsApp media (image) message via Evolution API.
    
    Args:
        instance_id: The tenant/instance ID
        phone_number: Recipient phone number
        media_url: URL of the media to send
        caption: Caption for the media
    
    Returns:
        Tuple of (status_code, response_text)
    """
    url = f"{EVOLUTION_API_BASE_URL}/message/sendMedia/{instance_id}"
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    payload = {
        "number": phone_number,
        "mediatype": "image",
        "media": media_url,
        "caption": caption
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload, headers=headers)
            return resp.status_code, resp.text
    except Exception as e:
        # Log error but don't crash webhook
        print(f"WhatsApp Media API error: {str(e)}")
        return None, str(e)


async def send_whatsapp_message(instance_id: str, phone_number: str, message_text: str) -> tuple[Optional[int], Optional[str]]:
    """
    Send WhatsApp message via Evolution API.
    
    Args:
        instance_id: The tenant/instance ID
        phone_number: Recipient phone number
        message_text: The message to send
    
    Returns:
        Tuple of (status_code, response_text)
    """
    url = f"{EVOLUTION_API_BASE_URL}/message/sendText/{instance_id}"
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    payload = {
        "number": phone_number,
        "text": message_text
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload, headers=headers)
            return resp.status_code, resp.text
    except Exception as e:
        # Log error but don't crash webhook
        print(f"WhatsApp API error: {str(e)}")
        return None, str(e)


@router.post("/messages-upsert")
async def webhook_handler(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handle webhook events from WhatsApp.
    
    Flow:
    1. If from user (fromMe=False):
       - Check if user exists by tenant_id + phone_no, create if not
       - Save user message to DB
       - Retrieve conversation history
       - Generate agent response using sales agent
       - Send response via WhatsApp API
       - Save agent response to DB
    
    2. If from assistant (fromMe=True):
       - Just save the message to DB (no agent response needed)
    """
    try:
        # Log incoming webhook request
        print("\n" + "="*60)
        print("🔔 WEBHOOK RECEIVED!")
        print("="*60)
        
        payload = await request.json()
        print(f"📦 Payload received: {json.dumps(payload, indent=2)}")
        
        # Evolution API sends data as a list of messages
        data_list = payload.get("data", [])
        
        # Handle both list and single object formats
        if isinstance(data_list, list):
            if not data_list:
                return JSONResponse(content={"status": "skipped", "message": "Empty data list"})
            # Get the first message from the list
            data = data_list[0]
        else:
            # Fallback for single object format
            data = data_list
        
        key = data.get("key", {}) or {}

        from_me = key.get("fromMe", False)
        instance = payload.get("instance")  # tenant/instance id
        date_time = payload.get("date_time")
        raw_message_obj = data.get("message", {}) or {}
        
        print(f"📌 Instance: {instance}")
        print(f"📌 From Me: {from_me}")
        print(f"📌 Date/Time: {date_time}")

        # Make sure instance exists
        if not instance:
            raise HTTPException(status_code=400, detail="Missing instance/tenant id in payload")

        # Normalize tenant id as UUID if possible
        try:
            tenant_id = UUID(instance)
        except Exception:
            # If not a valid UUID, try to keep it as string but this might cause issues
            raise HTTPException(status_code=400, detail="Invalid instance/tenant id format")

        # Extract phone number and message content
        if from_me:
            # Message sent by assistant (outbound)
            sender = payload.get("sender", "") or key.get("remoteJid", "")
            sender_phone = sender.split("@")[0] if sender else None
            message_text = raw_message_obj.get("conversation") or raw_message_obj.get("extendedTextMessage", {}).get("text")
            role = "assistant"
        else:
            # Message from user (inbound)
            remote_jid = key.get("remoteJid", "")
            sender_phone = remote_jid.split("@")[0] if remote_jid else None
            message_text = raw_message_obj.get("conversation") or raw_message_obj.get("extendedTextMessage", {}).get("text")
            role = "user"

        if not sender_phone:
            raise HTTPException(status_code=400, detail="Missing or invalid phone number in webhook payload")

        if not message_text:
            # Skip non-text messages (images, etc.)
            return JSONResponse(content={"status": "skipped", "message": "Non-text message ignored"})

        # CASE 1: Message from USER (inbound) - fromMe=False
        if not from_me:
            # Get or create user by phone & tenant
            user = await get_user_by_phone(db, sender_phone, tenant_id)

            if user is None:
                # Create new user - handle race condition where user might be created between check and create
                try:
                    push_name = data.get("pushName") or payload.get("pushName")
                    user = await create_user(db, tenant_id=tenant_id, phone_no=sender_phone, name=push_name)
                    print(f"Successfully created new user: {sender_phone}")
                except ValueError as ve:
                    # User was created by another concurrent request, fetch it
                    print(f"ValueError creating user (already exists): {ve}")
                    await db.rollback()  # Rollback the failed transaction
                    user = await get_user_by_phone(db, sender_phone, tenant_id)
                    if not user:
                        # Still None? Something is wrong
                        raise HTTPException(status_code=500, detail="Failed to get or create user")
                    print(f"Successfully fetched existing user after ValueError: {sender_phone}")
                except Exception as e:
                    # Catch database unique constraint errors
                    print(f"Error creating user, attempting to fetch: {e}")
                    try:
                        await db.rollback()  # Rollback the failed transaction before querying
                        user = await get_user_by_phone(db, sender_phone, tenant_id)
                        if not user:
                            raise HTTPException(status_code=500, detail="Failed to get or create user after rollback")
                        print(f"Successfully fetched existing user after exception: {sender_phone}")
                    except Exception as fetch_error:
                        print(f"Failed to fetch user after rollback: {fetch_error}")
                        raise HTTPException(status_code=500, detail=f"Failed to get or create user: {str(fetch_error)}")

            # Save the incoming user message (query by tenant_id + phone_no)
            new_msg = UserMessage(
                tenant_id=tenant_id,
                phone_no=sender_phone,
                role=role,
                content=message_text
            )
            db.add(new_msg)
            await db.flush()

            # Retrieve last 30 exchanges of conversation history for this user (tenant_id + phone_no)
            stmt = select(UserMessage).where(
                UserMessage.tenant_id == tenant_id,
                UserMessage.phone_no == sender_phone,
            ).order_by(UserMessage.created_at.desc()).limit(30)
            result = await db.execute(stmt)
            messages = result.scalars().all()

            # Reverse to get chronological order and build history for agent as role/content dicts
            history = [{"role": m.role, "content": m.content or ""} for m in reversed(messages)]

            # Generate agent reply using sales agent (now with phone_number for media sending)
            agent_reply = await generate_agent_reply(message_text, history, tenant_id, sender_phone, db)

            # Send the response via WhatsApp Evolution API
            status_code, response_text = await send_whatsapp_message(
                instance_id=instance,
                phone_number=sender_phone,
                message_text=agent_reply
            )

            # Save assistant response in DB (query by tenant_id + phone_no)
            assistant_msg = UserMessage(
                tenant_id=tenant_id,
                phone_no=sender_phone,
                role="assistant",
                content=agent_reply
            )
            db.add(assistant_msg)
            await db.commit()

            return JSONResponse(content={
                "status": "success",
                "message": "User message saved, agent response generated and sent",
                "agent_reply": agent_reply,
                "send_status": status_code
            })

        # CASE 2: Message from ASSISTANT (outbound - fromMe=True)
        else:
            # Get or create user (in case assistant sent first message)
            user = await get_user_by_phone(db, sender_phone, tenant_id)
            if user is None:
                # Create placeholder user - handle race condition
                try:
                    user = await create_user(db, tenant_id=tenant_id, phone_no=sender_phone, name=None)
                    print(f"Successfully created new user for assistant message: {sender_phone}")
                except ValueError as ve:
                    # User was created by another concurrent request, fetch it
                    print(f"ValueError creating user (already exists): {ve}")
                    await db.rollback()  # Rollback the failed transaction
                    user = await get_user_by_phone(db, sender_phone, tenant_id)
                    if not user:
                        raise HTTPException(status_code=500, detail="Failed to get or create user")
                    print(f"Successfully fetched existing user after ValueError: {sender_phone}")
                except Exception as e:
                    # Catch database unique constraint errors
                    print(f"Error creating user, attempting to fetch: {e}")
                    try:
                        await db.rollback()  # Rollback the failed transaction before querying
                        user = await get_user_by_phone(db, sender_phone, tenant_id)
                        if not user:
                            raise HTTPException(status_code=500, detail="Failed to get or create user after rollback")
                        print(f"Successfully fetched existing user after exception: {sender_phone}")
                    except Exception as fetch_error:
                        print(f"Failed to fetch user after rollback: {fetch_error}")
                        raise HTTPException(status_code=500, detail=f"Failed to get or create user: {str(fetch_error)}")

            # Just save the assistant message (query by tenant_id + phone_no)
            assistant_msg = UserMessage(
                tenant_id=tenant_id,
                phone_no=sender_phone,
                role=role,
                content=message_text
            )
            db.add(assistant_msg)
            await db.commit()

            return JSONResponse(content={
                "status": "success",
                "message": "Assistant message saved"
            })

    except HTTPException:
        raise
    except Exception as e:
        # Best-effort rollback if possible
        try:
            await db.rollback()
        except Exception:
            pass
        # Include error message for debugging
        print(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages-upsert")
async def webhook_health_check():
    print("✅ Webhook health check endpoint hit!")
    return {"status": "ok", "message": "Webhook is live and listening for POST events"}


@router.post("/connection-update")
async def connection_update_handler(request: Request):
    """
    Handle CONNECTION_UPDATE events from WhatsApp Evolution API.
    
    Simply logs the connection state to the terminal for monitoring.
    """
    try:
        print("\n" + "="*60)
        print("🔌 CONNECTION_UPDATE WEBHOOK RECEIVED!")
        print("="*60)
        
        payload = await request.json()
        
        # Extract instance (tenant_id) and status from the payload
        instance = payload.get("instance")
        
        # Handle both direct data and nested data structures
        data = payload.get("data", {})
        if isinstance(data, list):
            data = data[0] if data else {}
        
        # Try to get state/status from various possible paths in the payload
        state = (
            payload.get("state") or 
            payload.get("status") or 
            data.get("state") or 
            data.get("status") or
            data.get("instance", {}).get("state")
        )
        
        # Try to get date_time from various possible paths
        date_time = (
            payload.get("date_time") or
            payload.get("dateTime") or
            data.get("date_time") or
            data.get("dateTime") or
            datetime.now().isoformat()
        )
        
        # Display connection state info
        print(f"instance_name: {instance}")
        print(f"state: {state}")
        print(f"date & time: {date_time}")
        print("="*60 + "\n")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Connection update received and logged"
        })
        
    except Exception as e:
        print(f"❌ Connection update error: {str(e)}")
        return JSONResponse(content={
            "status": "error",
            "message": str(e)
        }, status_code=500)


@router.post("/test-webhook")
async def test_webhook(request: Request):
    """Test endpoint to verify webhook is receiving requests"""
    print("\n" + "="*60)
    print("🧪 TEST WEBHOOK HIT!")
    print("="*60)
    try:
        payload = await request.json()
        print(f"Received payload: {json.dumps(payload, indent=2)}")
        return JSONResponse(content={
            "status": "success",
            "message": "Test webhook received",
            "received_data": payload
        })
    except Exception as e:
        print(f"Error parsing payload: {e}")
        return JSONResponse(content={
            "status": "error",
            "message": str(e)
        }, 
        status_code=400)


        