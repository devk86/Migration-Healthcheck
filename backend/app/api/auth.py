from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.errors import AuthenticationFailed
from app.models import User
from app.schemas.comparison import LoginRequest, TokenRead
from app.security.passwords import verify_password
from app.security.tokens import create_token
from app.services.audit import record

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenRead)
def login(payload: LoginRequest, session: DbSession) -> TokenRead:
    user = session.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        record(session, payload.username, "auth.login_failed", payload.username)
        session.commit()
        raise AuthenticationFailed("Username or password is incorrect.")
    record(session, user.username, "auth.login", user.username)
    session.commit()
    return TokenRead(
        access_token=create_token(user.id, user.role),
        role=user.role,
        username=user.username,
    )


@router.get("/me")
def me(user: CurrentUser) -> dict[str, str]:
    return {"username": user.username, "role": user.role}
