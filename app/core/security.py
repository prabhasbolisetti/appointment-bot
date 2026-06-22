import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import get_settings
from werkzeug.security import check_password_hash, generate_password_hash

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except Exception:
    bcrypt = None
    BCRYPT_AVAILABLE = False


def hash_password(password: str) -> str:
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("$2"):
        return BCRYPT_AVAILABLE and bcrypt.checkpw(password.encode(), password_hash.encode())
    return check_password_hash(password_hash, password)


def create_access_token(admin_id: str, clinic_id: str = None, expires_delta: timedelta = None) -> str:
    if expires_delta is None:
        expires_delta = timedelta(hours=24)

    settings = get_settings()
    clinic_id = clinic_id or settings.CLINIC_ID
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": admin_id,
        "admin_id": admin_id,
        "clinic_id": clinic_id,
        "exp": expire
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token


def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
