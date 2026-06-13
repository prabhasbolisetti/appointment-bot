from app.core.database import get_db


def get_appointments_by_clinic(clinic_id: str, status: str = None):
    db = get_db()

    query = (
        db.table("appointments")
        .select(
            "id, patient_id, slot_id, clinic_id, status, payment_status, reminder_sent, created_at"
        )
        .eq("clinic_id", clinic_id)
        .order("created_at", desc=True)
    )

    if status:
        query = query.eq("status", status)

    response = query.execute()
    return response.data


def get_appointment(appointment_id: str):
    db = get_db()

    response = (
        db.table("appointments")
        .select("*")
        .eq("id", appointment_id)
        .single()
        .execute()
    )

    return response.data if response.data else None


def cancel_appointment(appointment_id: str):
    db = get_db()

    db.table("appointments").update({
        "status": "cancelled"
    }).eq("id", appointment_id).execute()


def complete_appointment(appointment_id: str):
    db = get_db()

    db.table("appointments").update({
        "status": "completed"
    }).eq("id", appointment_id).execute()