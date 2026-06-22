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
    email: Optional[str] = None
    age: Optional[int] = None
    conversation_state: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
