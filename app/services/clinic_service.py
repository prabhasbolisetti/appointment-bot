from app.core.database import get_db


def get_clinic(clinic_id: str) -> dict:
    db = get_db()
    response = (
        db.table("clinics")
        .select("*")
        .eq("id", clinic_id)
        .single()
        .execute()
    )
    return response.data if response.data else None


def update_clinic(clinic_id: str, data: dict) -> dict:
    db = get_db()
    response = (
        db.table("clinics")
        .update(data)
        .eq("id", clinic_id)
        .execute()
    )
    return response.data[0] if response.data else None