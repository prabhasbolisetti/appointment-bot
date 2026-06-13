from pydantic import BaseModel
from datetime import time
from uuid import UUID
from typing import Optional


class ClinicResponse(BaseModel):
    id: UUID
    name: str
    address: str
    google_map_link: Optional[str]
    open_time: time
    close_time: time
    slot_duration_minutes: int
    consultation_fee: float
    is_active: bool

    class Config:
        from_attributes = True


class ClinicUpdateRequest(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    google_map_link: Optional[str] = None
    open_time: Optional[time] = None
    close_time: Optional[time] = None
    slot_duration_minutes: Optional[int] = None
    consultation_fee: Optional[float] = None
    is_active: Optional[bool] = None