import uuid

from fastapi import APIRouter, Response
from sqlalchemy import select

from app.api.deps import Admin, CurrentUser, DbSession, Writer
from app.connectors.base import BaseConnector
from app.errors import NotFoundError
from app.models import Server
from app.schemas.common import ServerRead
from app.schemas.healthcheck import SnapshotRead
from app.schemas.server import ConnectionTestRead, ServerCreate, ServerUpdate
from app.security.crypto import decrypt_secret
from app.services import server_service
from app.services.collection_runner import _connector
from app.services.credential_service import resolve_credential

router = APIRouter(prefix="/servers", tags=["servers"])


def _read(session: DbSession, server: Server) -> ServerRead:
    data = ServerRead.model_validate(server)
    data.current_status = server_service.latest_status(session, server.id)
    return data


@router.get("", response_model=list[ServerRead])
def list_servers(
    session: DbSession,
    user: CurrentUser,
    os_type: str | None = None,
    enabled: bool | None = None,
    wave: str | None = None,
    q: str | None = None,
) -> list[ServerRead]:
    _ = user
    servers = server_service.search_servers(
        session, os_type=os_type, enabled=enabled, wave=wave, query=q
    )
    return [_read(session, server) for server in servers]


@router.post("", response_model=ServerRead, status_code=201)
async def create_server(payload: ServerCreate, session: DbSession, user: Writer) -> ServerRead:
    server = await server_service.create_server(
        session,
        name=payload.name,
        address=payload.address,
        os_type=payload.os_type,
        enabled=payload.enabled,
        wave=payload.wave,
        actor=user.username,
    )
    return _read(session, server)


@router.get("/{server_id}", response_model=ServerRead)
def get_server(server_id: uuid.UUID, session: DbSession, user: CurrentUser) -> ServerRead:
    _ = user
    server = session.get(Server, server_id)
    if server is None:
        raise NotFoundError("Server was not found.")
    return _read(session, server)


@router.patch("/{server_id}", response_model=ServerRead)
def update_server(
    server_id: uuid.UUID,
    payload: ServerUpdate,
    session: DbSession,
    user: Writer,
) -> ServerRead:
    server = server_service.update_server(
        session,
        server_id,
        payload.model_dump(exclude_unset=True),
        user.username,
    )
    return _read(session, server)


@router.delete("/{server_id}", status_code=204)
async def delete_server(server_id: uuid.UUID, session: DbSession, user: Admin) -> Response:
    await server_service.delete_server(session, server_id, user.username)
    return Response(status_code=204)


@router.get("/{server_id}/snapshots", response_model=list[SnapshotRead])
def list_snapshots(server_id: uuid.UUID, session: DbSession, user: CurrentUser) -> list[SnapshotRead]:
    _ = user
    server = session.get(Server, server_id)
    if server is None:
        raise NotFoundError("Server was not found.")
    from app.models import Snapshot

    rows = session.scalars(
        select(Snapshot).where(Snapshot.server_id == server_id).order_by(Snapshot.created_at.desc())
    )
    return [SnapshotRead.model_validate(row) for row in rows]


@router.post("/{server_id}/test-connection", response_model=ConnectionTestRead)
async def test_connection(server_id: uuid.UUID, session: DbSession, user: Writer) -> ConnectionTestRead:
    server = session.get(Server, server_id)
    if server is None:
        raise NotFoundError("Server was not found.")
    credential = resolve_credential(session, server)
    if credential is None:
        from datetime import UTC, datetime

        server.last_connection_status = "AUTHENTICATION_ERROR"
        server.last_connection_checked_at = datetime.now(UTC)
        session.commit()
        return ConnectionTestRead(
            ok=False,
            code="AUTHENTICATION_ERROR",
            message="Credential is required.",
            server_id=server.id,
        )
    secret = decrypt_secret(credential.secret_encrypted)
    connector: BaseConnector = _connector(server, credential.username, secret, credential.kind, "PRE")
    result = await connector.test_connection()
    from datetime import UTC, datetime

    server.last_connection_status = "ok" if result.ok else result.code
    server.last_connection_checked_at = datetime.now(UTC)
    session.commit()
    return ConnectionTestRead(ok=result.ok, code=result.code, message=result.message, server_id=server.id)

