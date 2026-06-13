from app.core.database import get_db


def get_patients_by_clinic(clinic_id: str):
    db = get_db()

    response = (
        db.table("patients")
        .select("*")
        .execute()
    )

    return response.data


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