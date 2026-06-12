import json
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from app.core.config import get_settings
from app.services import whatsapp_service

logger = logging.getLogger("appointment.whatsapp")

router = APIRouter(prefix="/webhook", tags=["whatsapp"])


def _mask_auth(headers: dict) -> dict:
    """Mask sensitive Authorization header for safe logging."""
    h = dict(headers)
    for k in list(h.keys()):
        if k.lower() == "authorization":
            h[k] = "<REDACTED>"
    return h


@router.get("/")
def verify_webhook(request: Request):
    settings = get_settings()
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    logger.debug("GET /webhook/ verify request params: %s", params)

    if mode == "subscribe" and token == settings.WEBHOOK_VERIFY_TOKEN:
        logger.info("✅ Webhook verified by Meta")
        return PlainTextResponse(content=challenge)

    logger.warning("Webhook verification failed: mode=%s token=%s", mode, token)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/")
async def receive_message(request: Request):
    logger.info("🔔 POST /webhook/ REQUEST RECEIVED")

    # Log headers (mask auth)
    try:
        raw_headers = dict(request.headers)
        logger.debug("Request headers: %s", json.dumps(_mask_auth(raw_headers), indent=2))
    except Exception:
        logger.exception("Failed to read request headers")

    try:
        body = await request.json()
        logger.debug("Raw body: %s", json.dumps(body, indent=2))
    except Exception as e:
        logger.exception("Failed to parse JSON body: %s", e)
        # Return 200 to keep Meta happy; it will retry on non-2xx
        return JSONResponse(status_code=200, content={"status": "ok"})

    try:
        entry = body["entry"][0]
        logger.debug("Got entry")

        changes = entry["changes"][0]
        logger.debug("Got changes: %s", json.dumps(changes, indent=2))

        value = changes["value"]
        logger.debug("Got value: %s", json.dumps(value, indent=2))

        # Ignore status updates
        if "statuses" in value:
            logger.info("⏭️  Ignoring status update")
            return JSONResponse(status_code=200, content={"status": "ok"})

        messages = value.get("messages", [])
        logger.debug("Messages list length: %d", len(messages))

        if not messages:
            logger.info("⏭️  No messages in payload")
            return JSONResponse(status_code=200, content={"status": "ok"})

        message = messages[0]
        from_number = message.get("from")
        message_type = message.get("type")

        logger.info("📱 Message from %s, type: %s", from_number, message_type)

        if message_type == "text":
            text = message["text"]["body"].strip().lower()
            logger.info("📝 Text content: '%s'", text)
            logger.info("🚀 Calling handle_text_message...")
            await whatsapp_service.handle_text_message(from_number, text)
            logger.info("✅ handle_text_message completed")

        elif message_type == "interactive":
            interactive = message["interactive"]
            if interactive.get("type") == "button_reply":
                button_id = interactive["button_reply"]["id"]
                await whatsapp_service.handle_button_reply(from_number, button_id)
            elif interactive.get("type") == "list_reply":
                list_id = interactive["list_reply"]["id"]
                await whatsapp_service.handle_list_reply(from_number, list_id)

    except KeyError as e:
        logger.exception("KeyError while processing webhook payload: %s", e)
    except Exception as e:
        logger.exception("Unexpected error while processing webhook: %s", e)

    return JSONResponse(status_code=200, content={"status": "ok"})