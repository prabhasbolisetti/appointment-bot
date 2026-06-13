import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import get_settings
from uuid import UUID


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(admin_id: str, clinic_id: str, expires_delta: timedelta = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(hours=24)

    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "admin_id": admin_id,
        "clinic_id": clinic_id,
        "exp": expire
    }
    token = jwt.encode(payload, get_settings().WEBHOOK_VERIFY_TOKEN, algorithm="HS256")
    return token


def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, get_settings().WEBHOOK_VERIFY_TOKEN, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None