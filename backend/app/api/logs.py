import uuid

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.errors import NotFoundError
from app.models import HealthCheckRun, Snapshot
from app.storage.local import log_storage

router = APIRouter(tags=["logs"])


@router.get("/healthchecks/{run_id}/logs")
async def run_logs(
    run_id: uuid.UUID,
    session: DbSession,
    user: CurrentUser,
    server_id: uuid.UUID | None = None,
) -> dict[str, object]:
    _ = user
    if session.get(HealthCheckRun, run_id) is None:
        raise NotFoundError("Health check was not found.")
    stmt = select(Snapshot).where(Snapshot.run_id == run_id)
    if server_id is not None:
        stmt = stmt.where(Snapshot.server_id == server_id)
    snapshots = list(session.scalars(stmt))
    logs = []
    for snapshot in snapshots:
        payload = await log_storage().load(snapshot.log_path)
        payload["server_id"] = str(snapshot.server_id)
        payload["phase"] = snapshot.phase
        logs.append(payload)
    return {"logs": logs}


@router.get("/servers/{server_id}/logs")
async def server_logs(server_id: uuid.UUID, session: DbSession, user: CurrentUser) -> dict[str, object]:
    _ = user
    snapshots = list(
        session.scalars(select(Snapshot).where(Snapshot.server_id == server_id).order_by(Snapshot.created_at.desc()))
    )
    logs = []
    for snapshot in snapshots:
        payload = await log_storage().load(snapshot.log_path)
        payload["run_id"] = str(snapshot.run_id)
        payload["phase"] = snapshot.phase
        logs.append(payload)
    return {"logs": logs}
