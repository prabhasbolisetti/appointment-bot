from datetime import date, timedelta
from app.services.whatsapp_service import send_text, send_slots_list
from app.services.booking_service import hold_slot_for_patient, get_available_slots
from app.core.config import get_settings


CLINIC_ID = "6b49f5f1-bf68-40a6-82fd-d90acfebd428"


async def handle_book_appointment(from_number: str):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    slots = get_available_slots(CLINIC_ID, tomorrow)

    if not slots:
        await send_text(
            from_number,
            "😔 No available slots for tomorrow. Please try again later."
        )
        return

    await send_slots_list(from_number, slots)


async def handle_slot_selected(from_number: str, slot_id: str):
    result = hold_slot_for_patient(
        slot_id=slot_id,
        whatsapp_number=from_number
    )

    if not result["success"]:
        await send_text(from_number, result["message"])
        return

    await send_text(
        from_number,
        f"✅ Slot held for 5 minutes!\n\nAppointment ID: {result['appointment_id']}\n\n💳 Payment link coming next..."
    )