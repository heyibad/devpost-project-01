from typing import Optional
import httpx
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.security import get_current_tenant

# use AsyncSession and sqlmodel select for async DB access
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.tenant import Tenant
from app.models.whatsapp_cred import WhatsAppCred
from app.utils.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/instance_create")
async def create_instance(
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Create a new WhatsApp instance and generate QR code.
    Always creates a fresh instance regardless of existing records.
    """
    try:
        # Ensure Evolution API config exists
        if not settings.evolution_api_url or not settings.evolution_api_key:
            logger.error(
                "Evolution API config missing: url=%s key=%s",
                settings.evolution_api_url,
                bool(settings.evolution_api_key),
            )
            raise HTTPException(
                status_code=500,
                detail="Evolution API configuration is missing on server",
            )

        tenant_id = str(current_tenant.id)
        instance_name = tenant_id

        logger.info(f"Creating new WhatsApp instance for tenant {tenant_id}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try to delete existing instance first (cleanup any orphaned instances)
            try:
                delete_response = await client.delete(
                    f"{settings.evolution_api_url}/instance/delete/{instance_name}",
                    headers={"apikey": settings.evolution_api_key},
                )
                if delete_response.status_code in (200, 201, 204):
                    logger.info(f"Deleted existing instance {instance_name} before creating new one")
                else:
                    logger.debug(f"No existing instance to delete (status {delete_response.status_code})")
            except Exception as e:
                logger.debug(f"Instance deletion skipped (likely doesn't exist): {e}")

            # Always create a new instance
            create_response = await client.post(
                f"{settings.evolution_api_url}/instance/create",
                headers={
                    "Content-Type": "application/json",
                    "apikey": settings.evolution_api_key,
                },
                json={
                    "instanceName": instance_name,
                    "qrcode": True,
                    "integration": "WHATSAPP-BAILEYS",
                    "webhook": {
                        "url": settings.webhook_url,
                        "byEvents": True,
                        "base64": True,
                        "headers": {
                            "autorization": settings.evolution_api_key,
                            "Content-Type": "application/json",
                        },
                        "events": [
                            "MESSAGES_UPSERT",
                            "CONNECTION_UPDATE",
                        ],
                    },
                },
            )

            if create_response.status_code not in (200, 201):
                text = create_response.text
                logger.error(
                    "Evolution create failed: %s %s", create_response.status_code, text
                )
                raise HTTPException(
                    status_code=502, 
                    detail="Unable to connect to WhatsApp service. Please try again in a moment."
                )

            # Get QR code
            connect_response = await client.get(
                f"{settings.evolution_api_url}/instance/connect/{instance_name}",
                headers={"apikey": settings.evolution_api_key},
            )

            if connect_response.status_code != 200:
                text = connect_response.text
                logger.error(
                    "Evolution connect fetch failed: %s %s",
                    connect_response.status_code,
                    text,
                )
                raise HTTPException(
                    status_code=502, 
                    detail="Unable to generate QR code. Please try again."
                )

            # Normalize the connect response to always return a `qrcode` field
            try:
                connect_json = connect_response.json()
            except Exception:
                connect_json = {}

            # Strip data URI prefix if present
            def _strip_data_prefix(s: str) -> str:
                if not s:
                    return s
                if isinstance(s, str) and s.startswith("data:"):
                    parts = s.split("base64,", 1)
                    return parts[1] if len(parts) == 2 else s
                return s

            qrcode = None
            if isinstance(connect_json, dict):
                # Try different possible keys
                qrcode = connect_json.get("qrcode") or connect_json.get("qrCode")
                if not qrcode:
                    qrcode = connect_json.get("base64") or (
                        connect_json.get("data") or {}
                    ).get("base64")
                if qrcode:
                    qrcode = _strip_data_prefix(qrcode)

            # Save or update WhatsAppCred in database
            try:
                # Check if record already exists for this tenant
                result = await db.exec(
                    select(WhatsAppCred).where(WhatsAppCred.instance_name == tenant_id)
                )
                whatsapp_cred = result.first()

                if whatsapp_cred:
                    # Update existing record: update QR code and set is_active to False
                    whatsapp_cred.qr_code = qrcode
                    whatsapp_cred.is_active = False
                    logger.info(f"Updated WhatsAppCred for tenant {tenant_id}")
                else:
                    # Create new record with QR code and is_active = False
                    whatsapp_cred = WhatsAppCred(
                        instance_name=tenant_id, qr_code=qrcode, is_active=False
                    )
                    db.add(whatsapp_cred)
                    logger.info(f"Created new WhatsAppCred for tenant {tenant_id}")

                await db.commit()
                await db.refresh(whatsapp_cred)
            except Exception as db_error:
                logger.error(f"Database error saving WhatsAppCred: {db_error}")
                await db.rollback()
                
                # Cleanup: Delete the orphaned instance from Evolution API
                try:
                    await client.delete(
                        f"{settings.evolution_api_url}/instance/delete/{instance_name}",
                        headers={"apikey": settings.evolution_api_key},
                    )
                    logger.info(f"Cleaned up orphaned instance {instance_name} after DB error")
                except Exception:
                    logger.warning(f"Failed to cleanup instance {instance_name} after DB error")
                
                raise HTTPException(
                    status_code=500,
                    detail="Unable to save connection details. Please try again."
                )

            return JSONResponse(content={"qrcode": qrcode, "raw": connect_json})

    except httpx.ConnectError as e:
        logger.error(f"Cannot connect to Evolution API: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="WhatsApp service is currently unavailable. Please ensure the Evolution API is running."
        )
    except httpx.TimeoutException as e:
        logger.error(f"Evolution API timeout: {str(e)}")
        raise HTTPException(
            status_code=504,
            detail="Request timed out. The WhatsApp service might be slow. Please try again."
        )
    except httpx.RequestError as e:
        logger.exception("HTTPX request error: %s", e)
        raise HTTPException(
            status_code=503, 
            detail="Unable to reach WhatsApp service. Please check your connection and try again."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in create_instance: %s", e)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/instance_connect")
async def check_instance_connection(
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Check the connection state of WhatsApp instance from Evolution API.
    Updates database based on connection state:
    - If state is 'open': sets is_active = True
    - If instance doesn't exist: sets is_active = False
    """
    try:
        # Ensure Evolution API config exists
        if not settings.evolution_api_url or not settings.evolution_api_key:
            logger.error(
                "Evolution API config missing: url=%s key=%s",
                settings.evolution_api_url,
                bool(settings.evolution_api_key),
            )
            raise HTTPException(
                status_code=500,
                detail="Evolution API configuration is missing on server",
            )

        tenant_id = str(current_tenant.id)
        instance_name = tenant_id

        logger.debug("Checking connection state for instance %s", instance_name)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{settings.evolution_api_url}/instance/connectionState/{instance_name}",
                    headers={"apikey": settings.evolution_api_key},
                )

                # Log the raw response for debugging
                try:
                    response_json = response.json()
                except Exception:
                    response_json = {}
                
                logger.debug("Evolution connection state response: status=%s, body=%s", 
                            response.status_code, response_json)

                # Check if instance doesn't exist (404 or "Not Found" error)
                instance_not_found = (
                    response.status_code == 404 or
                    (isinstance(response_json, dict) and (
                        response_json.get("status") == 404 or
                        response_json.get("error") == "Not Found"
                    ))
                )

                if instance_not_found:
                    logger.info(f"Instance {instance_name} doesn't exist, marking as inactive")
                    
                    # Update database: set is_active to False
                    try:
                        result = await db.exec(
                            select(WhatsAppCred).where(
                                WhatsAppCred.instance_name == tenant_id
                            )
                        )
                        whatsapp_cred = result.first()

                        if whatsapp_cred:
                            whatsapp_cred.is_active = False
                            await db.commit()
                            await db.refresh(whatsapp_cred)
                            logger.info(f"Set is_active=False for tenant {tenant_id}")
                    except Exception as db_error:
                        logger.error(f"Database error updating is_active: {db_error}", exc_info=True)
                        await db.rollback()

                    return JSONResponse(
                        content={
                            "state": "not_found",
                            "is_connected": False,
                            "instance_exists": False,
                            "raw": response_json,
                        }
                    )

                # If response is not 200, return error
                if response.status_code != 200:
                    logger.error(
                        "Evolution state fetch failed: %s %s",
                        response.status_code,
                        response.text,
                    )
                    raise HTTPException(
                        status_code=502, detail="Failed to get connection state"
                    )

                # Normalize the response to find state
                def _find_state(obj):
                    """Recursively search for a 'state' key in nested dicts"""
                    if isinstance(obj, dict):
                        if "state" in obj:
                            return obj["state"]
                        for v in obj.values():
                            res = _find_state(v)
                            if res is not None:
                                return res
                    elif isinstance(obj, list):
                        for item in obj:
                            res = _find_state(item)
                            if res is not None:
                                return res
                    return None

                raw_state = _find_state(response_json)
                state = (
                    raw_state or response_json.get("instance", {}).get("state", "") or ""
                )
                
                logger.debug(
                    "Found state '%s' for instance %s (raw_state=%s)",
                    state,
                    instance_name,
                    raw_state,
                )

                # Check if connected (Evolution API returns 'open' when WhatsApp is connected)
                is_connected = (
                    state == "open" or
                    state == "connected" or
                    response_json.get("status") == "connected" or
                    (response_json.get("instance", {}) or {}).get("status") == "connected" or
                    (response_json.get("instance", {}) or {}).get("state") == "open"
                )

                if is_connected:
                    logger.info(
                        "Instance %s is now CONNECTED (state=%s)", instance_name, state
                    )

                    # Update is_active to True in WhatsAppCred table
                    try:
                        result = await db.exec(
                            select(WhatsAppCred).where(
                                WhatsAppCred.instance_name == tenant_id
                            )
                        )
                        whatsapp_cred = result.first()

                        if whatsapp_cred:
                            logger.info(
                                f"Found WhatsAppCred for tenant {tenant_id}, current is_active={whatsapp_cred.is_active}"
                            )
                            whatsapp_cred.is_active = True
                            await db.commit()
                            await db.refresh(whatsapp_cred)
                            logger.info(
                                f"Successfully set is_active=True for tenant {tenant_id}"
                            )
                        else:
                            logger.warning(
                                f"WhatsAppCred not found for tenant {tenant_id}, creating new record"
                            )
                            whatsapp_cred = WhatsAppCred(
                                instance_name=tenant_id, is_active=True
                            )
                            db.add(whatsapp_cred)
                            await db.commit()
                            await db.refresh(whatsapp_cred)
                            logger.info(
                                f"Created new WhatsAppCred with is_active=True for tenant {tenant_id}"
                            )
                    except Exception as db_error:
                        logger.error(
                            f"Database error updating is_active: {db_error}", exc_info=True
                        )
                        await db.rollback()
                else:
                    logger.debug(
                        f"Instance {instance_name} not connected yet (state={state})"
                    )

                return JSONResponse(
                    content={
                        "state": "connected" if is_connected else state,
                        "is_connected": is_connected,
                        "instance_exists": True,
                        "raw": response_json,
                    }
                )
        
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.TimeoutException) as e:
            logger.error(f"Failed to connect to Evolution API: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="WhatsApp service is currently unavailable. Please check if the Evolution API server is running and accessible."
            )

    except httpx.RequestError as e:
        logger.exception("HTTPX request error: %s", e)
        raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in check_instance_connection: %s", e)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/disconnect")
async def disconnect_whatsapp(
    db: AsyncSession = Depends(get_db),
    current_tenant: Tenant = Depends(get_current_tenant),
):
    """
    Disconnect WhatsApp instance by DELETING it from Evolution API.
    Frontend should poll /instance_connect to detect when instance is deleted,
    which will automatically update the database.
    """
    try:
        # Ensure Evolution API config exists
        if not settings.evolution_api_url or not settings.evolution_api_key:
            logger.error(
                "Evolution API config missing: url=%s key=%s",
                settings.evolution_api_url,
                bool(settings.evolution_api_key),
            )
            raise HTTPException(
                status_code=500,
                detail="Evolution API configuration is missing on server",
            )

        tenant_id = str(current_tenant.id)
        instance_name = tenant_id

        # Delete instance from Evolution API
        logger.info(f"Deleting WhatsApp instance {instance_name}")
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                delete_response = await client.delete(
                    f"{settings.evolution_api_url}/instance/delete/{instance_name}",
                    headers={"apikey": settings.evolution_api_key},
                )

                logger.info(
                    f"Evolution API delete response for {instance_name}: status={delete_response.status_code}"
                )

                # Evolution API might return different status codes for success
                # 200, 201, 204 are all considered successful
                if delete_response.status_code not in (200, 201, 204):
                    logger.warning(
                        f"Evolution API delete returned status {delete_response.status_code}: {delete_response.text}"
                    )
                    # Don't fail the request, frontend will poll to verify deletion
                else:
                    logger.info(
                        f"Successfully deleted instance {instance_name} from Evolution API"
                    )

        except httpx.RequestError as e:
            logger.error(f"HTTPX error during Evolution API delete: {e}")
            # Don't fail the disconnect, frontend will poll to verify
        except Exception as e:
            logger.error(f"Unexpected error during Evolution API delete: {e}")
            # Don't fail the disconnect, frontend will poll to verify

        # Return success - frontend will poll /instance_connect to verify deletion
        # and update the database when it detects instance doesn't exist
        return JSONResponse(
            content={
                "success": True,
                "message": "WhatsApp instance deletion initiated. Poll /instance_connect to verify.",
                "instance_name": instance_name,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error in disconnect_whatsapp: %s", e)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
