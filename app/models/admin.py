from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID


class AdminRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    clinic_id: UUID


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    clinic_id: UUID
    is_active: bool

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminResponse


class TokenPayload(BaseModel):
    admin_id: str
    clinic_id: str
    exp: int