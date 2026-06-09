from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse
from app.core.config import get_settings
from app.services import whatsapp_service

router = APIRouter(prefix="/webhook", tags=["whatsapp"])


@router.get("/")
def verify_webhook(request: Request):
    settings = get_settings()
    params = dict(request.query_params)

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WEBHOOK_VERIFY_TOKEN:
        print(f"✅ Webhook verified by Meta")
        return PlainTextResponse(content=challenge)

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/")
async def receive_message(request: Request):
    body = await request.json()

    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "statuses" in value:
            return {"status": "ok"}

        messages = value.get("messages", [])
        if not messages:
            return {"status": "ok"}

        message = messages[0]
        from_number = message["from"]
        message_type = message["type"]

        print(f"📱 Message from {from_number}, type: {message_type}")

        if message_type == "text":
            text = message["text"]["body"].strip().lower()
            await whatsapp_service.handle_text_message(from_number, text)

        elif message_type == "interactive":
            interactive = message["interactive"]
            if interactive["type"] == "button_reply":
                button_id = interactive["button_reply"]["id"]
                await whatsapp_service.handle_button_reply(from_number, button_id)
            elif interactive["type"] == "list_reply":
                list_id = interactive["list_reply"]["id"]
                await whatsapp_service.handle_list_reply(from_number, list_id)

    except (KeyError, IndexError) as e:
        print(f"⚠️ Could not parse message: {e}")

    return {"status": "ok"}