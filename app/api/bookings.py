from fastapi import APIRouter, HTTPException

from app.models.slot import HoldSlotRequest, HoldSlotResponse, SlotResponse
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/slots/{slot_date}", response_model=list[SlotResponse])
def get_slots(slot_date: str):
    slots = booking_service.get_available_slots(slot_date)
    if not slots:
        raise HTTPException(status_code=404, detail="No available slots for this date")
    return slots


@router.post("/hold", response_model=HoldSlotResponse)
def hold_slot(request: HoldSlotRequest):
    result = booking_service.hold_slot_for_patient(
        slot_id=str(request.slot_id),
        whatsapp_number=request.patient_whatsapp,
        patient_name=request.patient_name,
        patient_email=request.patient_email,
        patient_age=request.patient_age,
        complaint_notes=request.complaint_notes,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return HoldSlotResponse(**result)
