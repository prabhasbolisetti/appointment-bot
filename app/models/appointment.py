from pydantic import BaseModel
from datetime import datetime, date, time
from uuid import UUID
from typing import Optional


class AppointmentResponse(BaseModel):
    id: UUID
    patient_id: UUID
    slot_id: UUID
    clinic_id: UUID
    status: str
    payment_status: str
    reminder_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PatientWithAppointments(BaseModel):
    id: UUID
    whatsapp_number: str
    name: Optional[str]
    appointment_count: int