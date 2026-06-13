from fastapi import APIRouter, HTTPException, Depends, Header, Query
from datetime import date, timedelta
from typing import List
from app.core.security import verify_access_token
from app.services import slot_service
from app.models.slot import SlotResponse, CreateSlotsRequest

router = APIRouter(prefix="/admin/slots", tags=["admin-slots"])


def get_current_admin(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload


@router.get("/", response_model=List[SlotResponse])
def list_slots(
    clinic_id: str = Query(...),
    slot_date: str = Query(None),
    status: str = Query(None),
    current_admin: dict = Depends(get_current_admin)
):
    if current_admin["clinic_id"] != clinic_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    slots = slot_service.get_slots_by_clinic(clinic_id, slot_date, status)
    return slots


@router.post("/bulk-create")
def bulk_create_slots(
    request: CreateSlotsRequest,
    current_admin: dict = Depends(get_current_admin)
):
    if current_admin["clinic_id"] != str(request.clinic_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    count = slot_service.bulk_create_slots(
        clinic_id=str(request.clinic_id),
        start_date=request.start_date,
        end_date=request.end_date,
        open_time=request.open_time,
        close_time=request.close_time,
        slot_duration_minutes=request.slot_duration_minutes
    )
    
    return {"created": count, "message": f"{count} slots created"}


@router.delete("/{slot_id}")
def delete_slot(slot_id: str, current_admin: dict = Depends(get_current_admin)):
    slot = slot_service.get_slot(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    if slot["clinic_id"] != current_admin["clinic_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    slot_service.delete_slot(slot_id)
    return {"status": "deleted"}


@router.post("/{slot_id}/release")
def release_slot(slot_id: str, current_admin: dict = Depends(get_current_admin)):
    slot = slot_service.get_slot(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    if slot["clinic_id"] != current_admin["clinic_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    slot_service.release_slot(slot_id)
    return {"status": "released"}