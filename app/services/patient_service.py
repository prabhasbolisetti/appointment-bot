from app.core.database import get_db
from app.repositories import patient_repo


def get_patients_by_clinic(clinic_id: str):
    db = get_db()

    response = (
        db.table("patients")
        .select("*")
        .execute()
    )

    return response.data


def get_or_create_patient(whatsapp_number: str):
    return patient_repo.get_or_create_patient(whatsapp_number)


def get_patient_by_whatsapp(whatsapp_number: str):
    return patient_repo.get_patient_by_whatsapp(whatsapp_number)


def update_patient(patient_id: str, data: dict):
    return patient_repo.update_patient(patient_id, data)


def get_patient(patient_id: str):
    db = get_db()

    response = (
        db.table("patients")
        .select("*")
        .eq("id", patient_id)
        .single()
        .execute()
    )

    return response.data if response.data else None
