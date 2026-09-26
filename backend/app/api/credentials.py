import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, Writer
from app.schemas.common import CredentialRead, GlobalCredentialRead
from app.schemas.server import CredentialCreate
from app.services.credential_service import (
    list_credentials,
    list_global_credentials,
    set_credential,
    set_global_credential,
)

router = APIRouter(prefix="/servers/{server_id}/credentials", tags=["credentials"])
global_router = APIRouter(prefix="/credentials/global", tags=["credentials"])


@router.get("", response_model=list[CredentialRead])
def get_credentials(server_id: uuid.UUID, session: DbSession, user: CurrentUser) -> list[CredentialRead]:
    _ = user
    return [CredentialRead.model_validate(item) for item in list_credentials(session, server_id)]


@router.post("", response_model=CredentialRead, status_code=201)
def put_credential(
    server_id: uuid.UUID,
    payload: CredentialCreate,
    session: DbSession,
    user: Writer,
) -> CredentialRead:
    credential = set_credential(
        session,
        server_id,
        kind=payload.kind,
        username=payload.username,
        secret=payload.secret,
        actor=user.username,
    )
    return CredentialRead.model_validate(credential)


@global_router.get("", response_model=list[GlobalCredentialRead])
def get_global_credentials(session: DbSession, user: CurrentUser) -> list[GlobalCredentialRead]:
    _ = user
    return [GlobalCredentialRead.model_validate(item) for item in list_global_credentials(session)]


@global_router.put("/{os_type}", response_model=GlobalCredentialRead)
def put_global_credential(
    os_type: str,
    payload: CredentialCreate,
    session: DbSession,
    user: Writer,
) -> GlobalCredentialRead:
    credential = set_global_credential(
        session,
        os_type.strip().lower(),
        kind=payload.kind,
        username=payload.username,
        secret=payload.secret,
        actor=user.username,
    )
    return GlobalCredentialRead.model_validate(credential)
