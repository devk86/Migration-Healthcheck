import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.config import get_settings
from app.errors import AuthenticationFailed


def create_token(user_id: uuid.UUID, role: str) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(UTC) + timedelta(minutes=settings.jwt_ttl_minutes),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    if isinstance(token, bytes):
        return token.decode()
    return token


def decode_token(token: str) -> dict[str, str]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise AuthenticationFailed("Sign in again.") from exc
    subject = payload.get("sub")
    role = payload.get("role")
    if not isinstance(subject, str) or not isinstance(role, str):
        raise AuthenticationFailed("Sign in again.")
    return {"sub": subject, "role": role}
