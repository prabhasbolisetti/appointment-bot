from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_admin
from app.models.admin import AdminLoginRequest, TokenResponse
from app.services import admin_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(request: AdminLoginRequest):
    result = admin_service.login_admin(
        username=request.username.strip(),
        password=request.password,
    )
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])

    return TokenResponse(
        access_token=result["access_token"],
        admin=result["admin"],
    )


@router.post("/logout")
def logout():
    return {"success": True}


@router.get("/me")
def me(current_admin: dict = Depends(get_current_admin)):
    return current_admin["admin"]
