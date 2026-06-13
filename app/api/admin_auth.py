from fastapi import APIRouter, HTTPException
from app.models.admin import AdminRegisterRequest, AdminLoginRequest, TokenResponse
from app.services import admin_service

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


@router.post("/register", response_model=TokenResponse)
def register(request: AdminRegisterRequest):
    result = admin_service.register_admin(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        clinic_id=str(request.clinic_id)
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    return TokenResponse(
        access_token=result["access_token"],
        admin=result["admin"]
    )


@router.post("/login", response_model=TokenResponse)
def login(request: AdminLoginRequest):
    result = admin_service.login_admin(
        email=request.email,
        password=request.password
    )

    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])

    return TokenResponse(
        access_token=result["access_token"],
        admin=result["admin"]
    )