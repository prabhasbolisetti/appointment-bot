from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories import admin_repo


def _admin_response(admin: dict) -> dict:
    settings = get_settings()
    return {
        "id": admin["id"],
        "username": admin["username"],
        "email": admin.get("email"),
        "full_name": admin["full_name"],
        "clinic_id": admin.get("clinic_id") or settings.CLINIC_ID,
        "is_active": admin["is_active"],
    }


def create_admin(username: str, password: str, full_name: str, email: str = None) -> dict:
    settings = get_settings()
    existing = admin_repo.get_admin_by_username(username)
    if existing:
        return {"success": False, "message": "Username already exists"}

    admin = admin_repo.create_admin_user(
        username=username,
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        clinic_id=settings.CLINIC_ID,
    )
    if not admin:
        return {"success": False, "message": "Failed to create admin"}

    return {"success": True, "admin": _admin_response(admin)}


def login_admin(username: str, password: str) -> dict:
    settings = get_settings()
    admin = admin_repo.get_admin_by_username(username)
    if not admin:
        return {"success": False, "message": "Invalid username or password"}

    if not verify_password(password, admin["password_hash"]):
        return {"success": False, "message": "Invalid username or password"}

    if not admin["is_active"]:
        return {"success": False, "message": "Admin account is disabled"}

    if str(admin.get("clinic_id")) != settings.CLINIC_ID:
        return {"success": False, "message": "Admin is not assigned to this clinic"}

    admin_repo.update_last_login(admin["id"])
    token = create_access_token(admin["id"], settings.CLINIC_ID)

    return {
        "success": True,
        "access_token": token,
        "admin": _admin_response(admin),
    }


def get_admin_profile(admin_id: str) -> dict:
    settings = get_settings()
    admin = admin_repo.get_admin_by_id(admin_id)
    if not admin or not admin.get("is_active"):
        return None
    if str(admin.get("clinic_id")) != settings.CLINIC_ID:
        return None
    return _admin_response(admin)
