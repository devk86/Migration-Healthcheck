import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import NotFoundError, ValidationFailed
from app.models import Comparison, Server
from app.repositories.server_repository import get_server, list_servers
from app.services.audit import record
from app.storage.local import log_storage, snapshot_storage


async def create_server(
    session: Session,
    *,
    name: str,
    address: str,
    os_type: str,
    enabled: bool,
    wave: str | None,
    actor: str,
) -> Server:
    normalized = os_type.strip().lower()
    if normalized not in {"linux", "windows"}:
        raise ValidationFailed("OS must be linux or windows.")
    clean_name = name.strip()
    if not clean_name or not address.strip():
        raise ValidationFailed("Server name and address are required.")
    existing = session.scalar(select(Server).where(Server.name == clean_name))
    if existing is not None:
        raise ValidationFailed("A server with this name already exists.")
    server = Server(
        name=clean_name,
        address=address.strip(),
        os_type=normalized,
        enabled=enabled,
        wave=wave.strip() if wave else None,
    )
    session.add(server)
    record(session, actor, "server.create", clean_name)
    session.commit()
    session.refresh(server)
    return server


def update_server(
    session: Session,
    server_id: uuid.UUID,
    changes: dict[str, object],
    actor: str,
) -> Server:
    server = get_server(session, server_id)
    if server is None:
        raise NotFoundError("Server was not found.")
    if "name" in changes and isinstance(changes["name"], str):
        server.name = changes["name"].strip()
    if "address" in changes and isinstance(changes["address"], str):
        server.address = changes["address"].strip()
    if "os_type" in changes and isinstance(changes["os_type"], str):
        normalized = changes["os_type"].strip().lower()
        if normalized not in {"linux", "windows"}:
            raise ValidationFailed("OS must be linux or windows.")
        server.os_type = normalized
    if "enabled" in changes and isinstance(changes["enabled"], bool):
        server.enabled = changes["enabled"]
    if "wave" in changes:
        wave = changes["wave"]
        server.wave = wave.strip() if isinstance(wave, str) and wave.strip() else None
    server.updated_at = datetime.now(UTC)
    record(session, actor, "server.update", str(server.id))
    session.commit()
    session.refresh(server)
    return server


async def delete_server(session: Session, server_id: uuid.UUID, actor: str) -> None:
    server = get_server(session, server_id)
    if server is None:
        raise NotFoundError("Server was not found.")
    snapshots = snapshot_storage()
    logs = log_storage()
    for snapshot in list(server.snapshots):
        await snapshots.delete(snapshot.path)
        await snapshots.delete(snapshot.raw_path)
        try:
            await logs.load(snapshot.log_path)
        except NotFoundError:
            pass
    record(session, actor, "server.delete", server.name)
    session.delete(server)
    session.commit()


def latest_status(session: Session, server_id: uuid.UUID) -> str | None:
    comparison = session.scalar(
        select(Comparison).where(Comparison.server_id == server_id).order_by(Comparison.created_at.desc())
    )
    if comparison is None:
        return None
    return comparison.overall_status


def search_servers(
    session: Session,
    *,
    os_type: str | None,
    enabled: bool | None,
    wave: str | None,
    query: str | None,
) -> list[Server]:
    return list_servers(session, os_type=os_type, enabled=enabled, wave=wave, query=query)
