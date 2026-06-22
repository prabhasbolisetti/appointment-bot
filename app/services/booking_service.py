from app.core.config import get_settings
from app.core.database import get_db
from app.repositories import patient_repo, slot_repo


def get_available_slots(slot_date: str) -> list:
    return slot_repo.get_available_slots(get_settings().CLINIC_ID, slot_date) or []


def hold_slot_for_patient(
    slot_id: str,
    whatsapp_number: str,
    patient_name: str = None,
    patient_email: str = None,
    patient_age: int = None,
    complaint_notes: str = None,
) -> dict:
    db = get_db()
    settings = get_settings()

    patient = patient_repo.get_or_create_patient(whatsapp_number)
    patient_id = patient["id"]

    patient_updates = {
        "name": patient_name,
        "email": patient_email,
        "age": patient_age,
    }
    if any(value is not None for value in patient_updates.values()):
        patient = patient_repo.update_patient(patient_id, patient_updates) or patient

    slot = slot_repo.get_slot(slot_id)
    if not slot or slot["clinic_id"] != settings.CLINIC_ID:
        return {"success": False, "message": "Slot is not available for this clinic"}

    held = slot_repo.atomic_hold_slot(slot_id, patient_id)
    if not held:
        return {
            "success": False,
            "message": "Sorry, that slot was just taken. Please choose another.",
        }

    appointment = (
        db.table("appointments")
        .insert({
            "patient_id": patient_id,
            "slot_id": slot_id,
            "clinic_id": settings.CLINIC_ID,
            "status": "pending",
            "payment_status": "unpaid",
            "complaint_notes": complaint_notes,
        })
        .execute()
    )

    appointment_id = appointment.data[0]["id"]
    held_until = slot_repo.get_slot(slot_id).get("held_until")

    patient_repo.update_conversation_state(
        patient_id,
        "AWAITING_PAYMENT",
        {
            "slot_id": slot_id,
            "appointment_id": appointment_id,
            "complaint_notes": complaint_notes,
        },
    )

    return {
        "success": True,
        "message": "Slot held for 5 minutes. Complete payment to confirm.",
        "appointment_id": appointment_id,
        "slot_id": slot_id,
        "held_until": held_until,
    }


def confirm_booking(appointment_id: str) -> bool:
    db = get_db()

    appt = (
        db.table("appointments")
        .select("slot_id, patient_id")
        .eq("id", appointment_id)
        .single()
        .execute()
    )
    if not appt.data:
        return False

    slot_repo.confirm_slot(appt.data["slot_id"])

    db.table("appointments").update({
        "status": "confirmed",
        "payment_status": "paid",
    }).eq("id", appointment_id).execute()

    patient_repo.update_conversation_state(appt.data["patient_id"], "IDLE", {})
    return True
