from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class PatientCreate(BaseModel):
    whatsapp_number: str
    name: Optional[str] = None


class PatientResponse(BaseModel):
    id: UUID
    whatsapp_number: str
    name: Optional[str]
    conversation_state: str

    class Config:
        from_attributes = True