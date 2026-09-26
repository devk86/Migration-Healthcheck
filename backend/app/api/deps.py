import uuid
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.errors import AuthenticationFailed, AuthorizationFailed
from app.models import User
from app.security.tokens import decode_token

DbSession = Annotated[Session, Depends(get_db)]
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    token = credentials.credentials if credentials is not None else None
    if token is None and authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token:
        raise AuthenticationFailed("Sign in required.")
    payload = decode_token(token)
    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError as exc:
        raise AuthenticationFailed("Sign in again.") from exc
    user = session.get(User, user_id)
    if user is None:
        raise AuthenticationFailed("Sign in again.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_writer(user: CurrentUser) -> User:
    if user.role == "viewer":
        raise AuthorizationFailed("You do not have permission to change this.")
    return user


def require_admin(user: CurrentUser) -> User:
    if user.role != "admin":
        raise AuthorizationFailed("Admin permission is required.")
    return user


Writer = Annotated[User, Depends(require_writer)]
Admin = Annotated[User, Depends(require_admin)]
