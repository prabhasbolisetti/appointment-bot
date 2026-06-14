from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional
from uuid import UUID


class SlotResponse(BaseModel):
    id: UUID
    clinic_id: UUID
    slot_date: date
    start_time: time
    status: str
    held_by: Optional[UUID] = None
    held_until: Optional[datetime] = None

    class Config:
        from_attributes = True


class HoldSlotRequest(BaseModel):
    slot_id: UUID
    patient_whatsapp: str


class CreateSlotsRequest(BaseModel):
    clinic_id: UUID
    start_date: date
    end_date: date
    open_time: time
    close_time: time
    slot_duration_minutes: int


class HoldSlotResponse(BaseModel):
    success: bool
    message: str
    slot_id: Optional[UUID] = None
    held_until: Optional[datetime] = None
    appointment_id: Optional[UUID] = None