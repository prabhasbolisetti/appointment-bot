from app.repositories import slot_repo
from app.core.config import get_settings
from app.repositories import patient_repo
from datetime import date, timedelta
import re


def get_slot(slot_id: str):
    return slot_repo.get_slot(slot_id)


def get_slots_by_clinic(clinic_id: str, slot_date: str = None, status: str = None):
    return slot_repo.get_slots_by_clinic(clinic_id, slot_date, status)


def bulk_create_slots(
    clinic_id: str,
    start_date,
    end_date,
    open_time,
    close_time,
    slot_duration_minutes: int,
):
    return slot_repo.bulk_create_slots(
        clinic_id,
        start_date,
        end_date,
        open_time,
        close_time,
        slot_duration_minutes,
    )


def delete_slot(slot_id: str):
    return slot_repo.delete_slot(slot_id)


def release_slot(slot_id: str):
    return slot_repo.release_slot(slot_id)


def _profile_complete(patient: dict) -> bool:
    return bool(patient.get("name") and patient.get("age") and patient.get("email"))


def _state_data(patient: dict) -> dict:
    data = patient.get("state_data") or {}
    return data if isinstance(data, dict) else {}


async def handle_book_appointment(from_number: str):
    from app.services import whatsapp_service

    patient = patient_repo.get_or_create_patient(from_number)
    if not patient.get("name"):
        patient_repo.update_conversation_state(patient["id"], "AWAITING_NAME", {})
        await whatsapp_service.send_text(from_number, "Please reply with the patient's full name.")
        return

    if not patient.get("age"):
        patient_repo.update_conversation_state(patient["id"], "AWAITING_AGE", {})
        await whatsapp_service.send_text(from_number, "Please reply with the patient's age.")
        return

    if not patient.get("email"):
        patient_repo.update_conversation_state(patient["id"], "AWAITING_EMAIL", {})
        await whatsapp_service.send_text(from_number, "Please reply with the patient's email address.")
        return

    patient_repo.update_conversation_state(patient["id"], "AWAITING_COMPLAINT", {})
    await whatsapp_service.send_text(
        from_number,
        "Please reply with the complaint or reason for visit. Reply 'skip' if you do not want to add one.",
    )


async def handle_patient_detail_reply(from_number: str, text: str) -> bool:
    from app.services import whatsapp_service

    patient = patient_repo.get_patient_by_whatsapp(from_number)
    if not patient:
        return False

    state = patient.get("conversation_state")
    if state not in {"AWAITING_NAME", "AWAITING_AGE", "AWAITING_EMAIL", "AWAITING_COMPLAINT"}:
        return False

    if state == "AWAITING_NAME":
        name = text.strip()
        if len(name) < 2:
            await whatsapp_service.send_text(from_number, "Please send a valid patient name.")
            return True
        patient_repo.update_patient(patient["id"], {"name": name.title()})
        patient_repo.update_conversation_state(patient["id"], "AWAITING_AGE", {})
        await whatsapp_service.send_text(from_number, "Thanks. Please reply with the patient's age.")
        return True

    if state == "AWAITING_AGE":
        try:
            age = int(text.strip())
        except ValueError:
            await whatsapp_service.send_text(from_number, "Please send age as a number.")
            return True
        if age <= 0 or age > 120:
            await whatsapp_service.send_text(from_number, "Please send a valid age between 1 and 120.")
            return True
        patient_repo.update_patient(patient["id"], {"age": age})
        patient_repo.update_conversation_state(patient["id"], "AWAITING_EMAIL", {})
        await whatsapp_service.send_text(from_number, "Please reply with the patient's email address.")
        return True

    if state == "AWAITING_EMAIL":
        email = text.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            await whatsapp_service.send_text(from_number, "Please send a valid email address.")
            return True
        patient_repo.update_patient(patient["id"], {"email": email})
        patient_repo.update_conversation_state(patient["id"], "AWAITING_COMPLAINT", {})
        await whatsapp_service.send_text(
            from_number,
            "Please reply with the complaint or reason for visit. Reply 'skip' if you do not want to add one.",
        )
        return True

    complaint = "" if text.strip().lower() == "skip" else text.strip()
    patient_repo.update_conversation_state(
        patient["id"],
        "AWAITING_SLOT_SELECTION",
        {"complaint_notes": complaint},
    )
    await _send_tomorrow_slots(from_number)
    return True


async def _send_tomorrow_slots(from_number: str):
    from app.services import booking_service, whatsapp_service

    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    slots = booking_service.get_available_slots(tomorrow)
    if not slots:
        await whatsapp_service.send_text(
            from_number,
            "No slots are available for tomorrow. Please try again later.",
        )
        return

    await whatsapp_service.send_slots_list(from_number, slots)


async def handle_slot_selected(from_number: str, slot_id: str):
    from app.services import booking_service, whatsapp_service

    settings = get_settings()
    patient = patient_repo.get_or_create_patient(from_number)
    data = _state_data(patient)

    result = booking_service.hold_slot_for_patient(
        slot_id=slot_id,
        whatsapp_number=from_number,
        patient_name=patient.get("name"),
        patient_email=patient.get("email"),
        patient_age=patient.get("age"),
        complaint_notes=data.get("complaint_notes"),
    )

    if not result["success"]:
        await whatsapp_service.send_text(from_number, result["message"])
        await _send_tomorrow_slots(from_number)
        return

    payment_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/payment/{result['appointment_id']}"
    await whatsapp_service.send_text(
        from_number,
        f"Slot held for 5 mins. Please complete payment to confirm.\n\nClick here to pay: {payment_url}",
    )
