from app.core.database import get_db


def get_appointment_with_details(appointment_id: str) -> dict:
    """Get appointment with patient and slot details"""
    db = get_db()
    response = (
        db.table("appointments")
        .select("""
            id, patient_id, slot_id, clinic_id, status, payment_status,
            reminder_sent, created_at, updated_at,
            patients(whatsapp_number, name, conversation_state),
            slots(slot_date, start_time, clinic_id)
        """)
        .eq("id", appointment_id)
        .single()
        .execute()
    )
    return response.data if response.data else None


def get_appointments_with_details(clinic_id: str, status: str = None) -> list:
    """Get all appointments for clinic with details"""
    db = get_db()
    query = (
        db.table("appointments")
        .select("""
            id, patient_id, slot_id, clinic_id, status, payment_status,
            reminder_sent, created_at,
            patients(whatsapp_number, name),
            slots(slot_date, start_time)
        """)
        .eq("clinic_id", clinic_id)
        .order("created_at", desc=True)
    )
    
    if status:
        query = query.eq("status", status)
    
    response = query.execute()
    return response.data if response.data else []


def update_appointment_status(appointment_id: str, status: str) -> dict:
    db = get_db()
    response = (
        db.table("appointments")
        .update({"status": status})
        .eq("id", appointment_id)
        .execute()
    )
    return response.data[0] if response.data else None


def update_appointment_payment_status(appointment_id: str, payment_status: str) -> dict:
    db = get_db()
    response = (
        db.table("appointments")
        .update({"payment_status": payment_status})
        .eq("id", appointment_id)
        .execute()
    )
    return response.data[0] if response.data else None


def get_appointment_payment(appointment_id: str) -> dict:
    """Get payment record for appointment"""
    db = get_db()
    response = (
        db.table("payments")
        .select("*")
        .eq("appointment_id", appointment_id)
        .single()
        .execute()
    )
    return response.data if response.data else None