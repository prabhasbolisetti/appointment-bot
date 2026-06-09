from app.repositories import slot_repo, patient_repo
from app.core.database import get_db
from uuid import uuid4


def get_available_slots(clinic_id: str, slot_date: str) -> list:
    slots = slot_repo.get_available_slots(clinic_id, slot_date)
    if not slots:
        return []
    return slots


def hold_slot_for_patient(slot_id: str, whatsapp_number: str) -> dict:
    db = get_db()

    # Step 1 — get or create patient
    patient = patient_repo.get_or_create_patient(whatsapp_number)
    patient_id = patient["id"]

    # Step 2 — atomic hold
    held = slot_repo.atomic_hold_slot(slot_id, patient_id)
    if not held:
        return {
            "success": False,
            "message": "Sorry, that slot was just taken. Please choose another."
        }

    # Step 3 — create pending appointment
    appointment = (
        db.table("appointments")
        .insert({
            "patient_id": patient_id,
            "slot_id": slot_id,
            "clinic_id": _get_clinic_id_from_slot(slot_id),
            "status": "pending",
            "payment_status": "unpaid"
        })
        .execute()
    )
    appointment_id = appointment.data[0]["id"]

    # Step 4 — update patient state
    patient_repo.update_conversation_state(
        patient_id,
        "AWAITING_PAYMENT",
        {"slot_id": slot_id, "appointment_id": appointment_id}
    )

    return {
        "success": True,
        "message": "Slot held for 5 minutes. Complete payment to confirm.",
        "appointment_id": appointment_id,
        "slot_id": slot_id
    }


def confirm_booking(appointment_id: str) -> bool:
    db = get_db()

    # Get appointment to find slot
    appt = (
        db.table("appointments")
        .select("slot_id, patient_id")
        .eq("id", appointment_id)
        .single()
        .execute()
    )
    if not appt.data:
        return False

    slot_id = appt.data["slot_id"]
    patient_id = appt.data["patient_id"]

    # Confirm slot
    slot_repo.confirm_slot(slot_id)

    # Confirm appointment
    db.table("appointments").update({
        "status": "confirmed",
        "payment_status": "paid"
    }).eq("id", appointment_id).execute()

    # Reset patient state
    patient_repo.update_conversation_state(patient_id, "IDLE", {})

    return True


def _get_clinic_id_from_slot(slot_id: str) -> str:
    db = get_db()
    response = (
        db.table("slots")
        .select("clinic_id")
        .eq("id", slot_id)
        .single()
        .execute()
    )
    return response.data["clinic_id"]