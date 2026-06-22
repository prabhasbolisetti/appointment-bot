from app.core.database import get_db


def get_or_create_patient(whatsapp_number: str) -> dict:
    db = get_db()

    response = (
        db.table("patients")
        .select("*")
        .eq("whatsapp_number", whatsapp_number)
        .execute()
    )

    if response.data and len(response.data) > 0:
        return response.data[0]

    # Create new patient
    new_patient = (
        db.table("patients")
        .insert({"whatsapp_number": whatsapp_number})
        .execute()
    )
    return new_patient.data[0]


def get_patient_by_whatsapp(whatsapp_number: str) -> dict:
    db = get_db()
    response = (
        db.table("patients")
        .select("*")
        .eq("whatsapp_number", whatsapp_number)
        .execute()
    )
    return response.data[0] if response.data and len(response.data) > 0 else None


def update_patient(patient_id: str, data: dict) -> dict:
    db = get_db()
    clean_data = {key: value for key, value in data.items() if value is not None}
    if not clean_data:
        return get_patient_by_id(patient_id)

    response = (
        db.table("patients")
        .update(clean_data)
        .eq("id", patient_id)
        .execute()
    )
    return response.data[0] if response.data else None


def get_patient_by_id(patient_id: str) -> dict:
    db = get_db()
    response = (
        db.table("patients")
        .select("*")
        .eq("id", patient_id)
        .single()
        .execute()
    )
    return response.data if response.data else None


def update_conversation_state(patient_id: str, state: str, state_data: dict = None) -> None:
    db = get_db()
    payload = {"conversation_state": state}
    if state_data is not None:
        payload["state_data"] = state_data

    db.table("patients").update(payload).eq("id", patient_id).execute()
