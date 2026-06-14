from fastapi import APIRouter, HTTPException, Depends, Header
from app.core.security import verify_access_token
from pydantic import BaseModel
from app.core.database import get_db

router = APIRouter(prefix="/admin/email-settings", tags=["email-settings"])


class EmailSettingsUpdate(BaseModel):
    send_booking_confirmation: bool = True
    send_reminders: bool = True
    send_cancellation_notification: bool = True
    reminder_hours_before: int = 1


def get_current_admin(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload


@router.get("/")
def get_email_settings(current_admin: dict = Depends(get_current_admin)):
    """Get email notification settings for clinic"""
    db = get_db()
    
    # For now, return default settings
    # In production, store these in a clinic_settings table
    return {
        "clinic_id": current_admin["clinic_id"],
        "send_booking_confirmation": True,
        "send_reminders": True,
        "send_cancellation_notification": True,
        "reminder_hours_before": 1
    }


@router.put("/")
def update_email_settings(
    settings: EmailSettingsUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update email notification settings"""
    # TODO: Save to clinic_settings table
    return {
        "success": True,
        "message": "Email settings updated",
        "clinic_id": current_admin["clinic_id"],
        "settings": settings.dict()
    }
from fastapi import APIRouter, HTTPException, Depends, Header
from app.core.security import verify_access_token
from pydantic import BaseModel, EmailStr
from app.core.database import get_db

router = APIRouter(prefix="/admin/email-settings", tags=["email-settings"])


class EmailSettingsUpdate(BaseModel):
    send_booking_confirmation: bool = True
    send_reminders: bool = True
    send_cancellation_notification: bool = True
    reminder_hours_before: int = 1


def get_current_admin(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    payload = verify_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload


@router.get("/")
def get_email_settings(current_admin: dict = Depends(get_current_admin)):
    """Get email notification settings for clinic"""
    db = get_db()
    
    # For now, return default settings
    # In production, store these in a clinic_settings table
    return {
        "clinic_id": current_admin["clinic_id"],
        "send_booking_confirmation": True,
        "send_reminders": True,
        "send_cancellation_notification": True,
        "reminder_hours_before": 1
    }


@router.put("/")
def update_email_settings(
    settings: EmailSettingsUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update email notification settings"""
    # TODO: Save to clinic_settings table
    return {
        "success": True,
        "message": "Email settings updated",
        "clinic_id": current_admin["clinic_id"],
        "settings": settings.dict()
    }