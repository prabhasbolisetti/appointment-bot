from fastapi import APIRouter, HTTPException, Depends, Header, Query
from app.core.security import verify_access_token
from app.services import patient_service
from app.models.patient import PatientResponse

router = APIRouter(prefix="/admin/patients", tags=["admin-patients"])


def get_current_admin(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload


@router.get("/", response_model=list[PatientResponse])
def list_patients(
    clinic_id: str = Query(...),
    current_admin: dict = Depends(get_current_admin)
):
    if current_admin["clinic_id"] != clinic_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    patients = patient_service.get_patients_by_clinic(clinic_id)
    return patients


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str):
    patient = patient_service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient