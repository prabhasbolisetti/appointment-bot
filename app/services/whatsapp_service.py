import httpx
from app.core.config import get_settings


def _get_headers():
    settings = get_settings()
    return {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }


def _get_url():
    settings = get_settings()
    return f"https://graph.facebook.com/v19.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"


async def send_text(to: str, message: str):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _get_url(),
            headers=_get_headers(),
            json=payload
        )
        print(f"📤 Sent to {to}: {response.status_code}")
        return response


async def send_main_menu(to: str):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "👋 Welcome to Sunrise Health Clinic!\n\nHow can I help you today?"
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
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _get_url(),
            headers=_get_headers(),
            json=payload
        )
        return response


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
            "body": {"text": "🗓️ Available slots for tomorrow.\n\nSelect a time:"},
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
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _get_url(),
            headers=_get_headers(),
            json=payload
        )
        return response


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
            "🕐 *Clinic Timings*\n\nMonday – Saturday\n9:00 AM – 5:00 PM\n\nSunday: Closed"
        )
    elif button_id == "CLINIC_LOCATION":
        await send_text(
            from_number,
            "📍 *Location*\n\n12-3, MG Road, Bhimavaram, AP 534202\n\nhttps://maps.google.com/?q=Bhimavaram"
        )


async def handle_list_reply(from_number: str, slot_id: str):
    from app.services.slot_service import handle_slot_selected
    await handle_slot_selected(from_number, slot_id)