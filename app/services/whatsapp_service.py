import json
import logging
import httpx
from app.core.config import get_settings

logger = logging.getLogger("appointment.whatsapp")


def _get_headers():
    settings = get_settings()
    return {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }


def _get_url():
    settings = get_settings()
    return f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"


def _mask_headers_for_log(headers: dict) -> dict:
    h = dict(headers)
    if "Authorization" in h:
        h["Authorization"] = "<REDACTED>"
    return h


async def _post(to: str, payload: dict):
    url = _get_url()
    headers = _get_headers()
    try:
        logger.debug("📤 Sending POST to WhatsApp API URL: %s", url)
        logger.debug("📤 Request headers: %s", json.dumps(_mask_headers_for_log(headers), indent=2))
        logger.debug("📤 Request payload: %s", json.dumps(payload, indent=2))

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=payload)

        # Try to log response body safely
        try:
            resp_text = response.text
            logger.info("📤 Response %s: %s", response.status_code, resp_text)
        except Exception:
            logger.info("📤 Response %s (no body)", response.status_code)

        return response
    except Exception as e:
        logger.exception("Failed to send message to WhatsApp API: %s", e)
        raise


async def send_text(to: str, message: str):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    return await _post(to, payload)


async def send_main_menu(to: str):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "👋 Welcome to Sunrise Health Clinic!\\n\\nHow can I help you today?"
            },
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "BOOK_APPOINTMENT", "title": "📅 Book Appointment"}},
                    {"type": "reply", "reply": {"id": "CLINIC_TIMINGS", "title": "🕐 Timings"}},
                    {"type": "reply", "reply": {"id": "CLINIC_LOCATION", "title": "📍 Location"}}
                ]
            }
        }
    }
    return await _post(to, payload)


async def send_slots_list(to: str, slots: list):
    """Send available slots as a WhatsApp list message."""
    rows = []
    for slot in slots[:10]:  # WhatsApp list max 10 items
        rows.append({
            "id": str(slot["id"]),
            "title": slot["start_time"][:5],  # "09:00"
            "description": f"Available slot"
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": "🗓️ Available slots for tomorrow.\\n\\nSelect a time:"},
            "action": {
                "button": "View Slots",
                "sections": [
                    {
                        "title": "Morning & Afternoon",
                        "rows": rows
                    }
                ]
            }
        }
    }
    return await _post(to, payload)


async def handle_text_message(from_number: str, text: str):
    greetings = ["hi", "hello", "hey", "start", "menu"]
    if any(g in text for g in greetings):
        await send_main_menu(from_number)
    else:
        await send_text(
            from_number,
            "Please type *Hi* to see the main menu."
        )


async def handle_button_reply(from_number: str, button_id: str):
    from app.services.slot_service import handle_book_appointment

    if button_id == "BOOK_APPOINTMENT":
        await handle_book_appointment(from_number)
    elif button_id == "CLINIC_TIMINGS":
        await send_text(
            from_number,
            "🕐 *Clinic Timings*\\n\\nMonday – Saturday\\n9:00 AM – 5:00 PM\\n\\nSunday: Closed"
        )
    elif button_id == "CLINIC_LOCATION":
        await send_text(
            from_number,
            "📍 *Location*\\n\\n12-3, MG Road, Bhimavaram, AP 534202\\n\\nhttps://maps.google.com/?q=Bhimavaram"
        )


async def handle_list_reply(from_number: str, slot_id: str):
    from app.services.slot_service import handle_slot_selected
    await handle_slot_selected(from_number, slot_id)