import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.errors import NotFoundError
from app.models import Snapshot
from app.storage.local import snapshot_storage

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.get("/{snapshot_id}")
async def read_snapshot(snapshot_id: uuid.UUID, session: DbSession, user: CurrentUser) -> dict[str, object]:
    _ = user
    snapshot = session.get(Snapshot, snapshot_id)
    if snapshot is None:
        raise NotFoundError("Snapshot was not found.")
    return await snapshot_storage().load(snapshot.path)
