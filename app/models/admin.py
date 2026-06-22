from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional


class AdminRegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminResponse(BaseModel):
    id: UUID
    username: str
    email: Optional[str] = None
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
