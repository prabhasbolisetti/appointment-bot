from fastapi import APIRouter, HTTPException, Depends, Header
from app.core.security import verify_access_token
from app.services import clinic_service
from app.models.clinic import ClinicResponse, ClinicUpdateRequest

router = APIRouter(prefix="/admin/clinic", tags=["admin-clinic"])


def get_current_admin(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload


@router.get("/{clinic_id}", response_model=ClinicResponse)
def get_clinic(clinic_id: str, current_admin: dict = Depends(get_current_admin)):
    # Verify admin owns this clinic
    if current_admin["clinic_id"] != clinic_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    clinic = clinic_service.get_clinic(clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    return clinic


@router.put("/{clinic_id}", response_model=ClinicResponse)
def update_clinic(clinic_id: str, request: ClinicUpdateRequest, current_admin: dict = Depends(get_current_admin)):
    if current_admin["clinic_id"] != clinic_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    clinic = clinic_service.update_clinic(clinic_id, request.dict(exclude_unset=True))
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    
    return clinic