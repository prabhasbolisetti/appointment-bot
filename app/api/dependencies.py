from fastapi import Header, HTTPException

from app.core.config import get_settings
from app.core.security import verify_access_token
from app.services import admin_service


def get_current_admin(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ", 1)[1]
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    settings = get_settings()
    if payload.get("clinic_id") != settings.CLINIC_ID:
        raise HTTPException(status_code=403, detail="Token is not valid for this clinic")

    admin = admin_service.get_admin_profile(payload["admin_id"])
    if not admin:
        raise HTTPException(status_code=401, detail="Admin account is inactive or missing")

    return {
        "admin_id": payload["admin_id"],
        "clinic_id": settings.CLINIC_ID,
        "admin": admin,
    }
