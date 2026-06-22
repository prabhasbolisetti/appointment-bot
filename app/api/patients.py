from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_admin
from app.services import patient_service
from app.models.patient import PatientResponse

router = APIRouter(prefix="/admin/patients", tags=["admin-patients"])


@router.get("/", response_model=list[PatientResponse])
def list_patients(current_admin: dict = Depends(get_current_admin)):
    return patient_service.get_patients_by_clinic(current_admin["clinic_id"])


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, current_admin: dict = Depends(get_current_admin)):
    patient = patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
