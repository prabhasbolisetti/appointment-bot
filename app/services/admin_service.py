from app.repositories import admin_repo
from app.core.security import hash_password, verify_password, create_access_token
from uuid import UUID


def register_admin(email: str, password: str, full_name: str, clinic_id: str) -> dict:
    # Check if email already exists
    existing = admin_repo.get_admin_by_email(email)
    if existing:
        return {"success": False, "message": "Email already registered"}

    # Hash password
    password_hash = hash_password(password)

    # Create admin user
    admin = admin_repo.create_admin_user(email, password_hash, full_name, clinic_id)
    if not admin:
        return {"success": False, "message": "Failed to create admin"}

    # Generate token
    token = create_access_token(admin["id"], admin["clinic_id"])

    return {
        "success": True,
        "access_token": token,
        "admin": {
            "id": admin["id"],
            "email": admin["email"],
            "full_name": admin["full_name"],
            "clinic_id": admin["clinic_id"],
            "is_active": admin["is_active"]
        }
    }


def login_admin(email: str, password: str) -> dict:
    admin = admin_repo.get_admin_by_email(email)
    if not admin:
        return {"success": False, "message": "Invalid email or password"}

    if not verify_password(password, admin["password_hash"]):
        return {"success": False, "message": "Invalid email or password"}

    if not admin["is_active"]:
        return {"success": False, "message": "Admin account is disabled"}

    # Update last login
    admin_repo.update_last_login(admin["id"])

    # Generate token
    token = create_access_token(admin["id"], admin["clinic_id"])

    return {
        "success": True,
        "access_token": token,
        "admin": {
            "id": admin["id"],
            "email": admin["email"],
            "full_name": admin["full_name"],
            "clinic_id": admin["clinic_id"],
            "is_active": admin["is_active"]
        }
    }