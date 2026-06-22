from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_admin
from app.models.clinic import ClinicResponse, ClinicUpdateRequest
from app.services import clinic_service

router = APIRouter(prefix="/admin/clinic", tags=["admin-clinic"])


@router.get("/", response_model=ClinicResponse)
def get_current_clinic(current_admin: dict = Depends(get_current_admin)):
    clinic = clinic_service.get_clinic(current_admin["clinic_id"])
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic


@router.get("/{clinic_id}", response_model=ClinicResponse)
def get_clinic(clinic_id: str, current_admin: dict = Depends(get_current_admin)):
    if current_admin["clinic_id"] != clinic_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    clinic = clinic_service.get_clinic(clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")

    return clinic


@router.put("/", response_model=ClinicResponse)
def update_current_clinic(
    request: ClinicUpdateRequest,
    current_admin: dict = Depends(get_current_admin),
):
    clinic = clinic_service.update_clinic(
        current_admin["clinic_id"],
        request.dict(exclude_unset=True),
    )
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic
