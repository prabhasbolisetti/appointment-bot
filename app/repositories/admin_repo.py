from app.core.database import get_db
from datetime import datetime, timezone


def create_admin_user(username: str, email: str, password_hash: str, full_name: str, clinic_id: str) -> dict:
    db = get_db()
    response = (
        db.table("admin_users")
        .insert({
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name,
            "clinic_id": clinic_id
        })
        .execute()
    )
    return response.data[0] if response.data else None


def get_admin_by_username(username: str) -> dict:
    db = get_db()
    response = (
        db.table("admin_users")
        .select("*")
        .eq("username", username)
        .execute()
    )
    return response.data[0] if response.data and len(response.data) > 0 else None


def get_admin_by_email(email: str) -> dict:
    db = get_db()
    response = (
        db.table("admin_users")
        .select("*")
        .eq("email", email)
        .execute()
    )
    return response.data[0] if response.data and len(response.data) > 0 else None


def get_admin_by_id(admin_id: str) -> dict:
    db = get_db()
    response = (
        db.table("admin_users")
        .select("*")
        .eq("id", admin_id)
        .single()
        .execute()
    )
    return response.data if response.data else None


def update_last_login(admin_id: str) -> None:
    db = get_db()
    db.table("admin_users").update({
        "last_login": datetime.now(timezone.utc).isoformat()
    }).eq("id", admin_id).execute()
