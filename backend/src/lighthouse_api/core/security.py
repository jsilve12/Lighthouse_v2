import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from lighthouse_api.core.config import settings


def create_jwt_token(data: dict) -> str:
    payload = {
        **data,
        "exp": datetime.now(UTC) + timedelta(hours=settings.jwt_expiration_hours),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_jwt_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def generate_api_key() -> str:
    return f"lh_{secrets.token_urlsafe(32)}"


def hash_api_key(key: str) -> str:
    return bcrypt.hashpw(key.encode(), bcrypt.gensalt()).decode()


def verify_api_key(key: str, hashed: str) -> bool:
    return bcrypt.checkpw(key.encode(), hashed.encode())
