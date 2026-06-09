from fastapi import APIRouter, HTTPException
from app.models.slot import HoldSlotRequest, HoldSlotResponse, SlotResponse
from app.services import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/slots/{clinic_id}/{slot_date}", response_model=list[SlotResponse])
def get_slots(clinic_id: str, slot_date: str):
    slots = booking_service.get_available_slots(clinic_id, slot_date)
    if not slots:
        raise HTTPException(status_code=404, detail="No available slots for this date")
    return slots


@router.post("/hold", response_model=HoldSlotResponse)
def hold_slot(request: HoldSlotRequest):
    result = booking_service.hold_slot_for_patient(
        slot_id=str(request.slot_id),
        whatsapp_number=request.patient_whatsapp
    )
    return HoldSlotResponse(**result)