from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.healthcheck import HealthCheckRead
from app.services.dashboard_service import dashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(
    session: DbSession,
    user: CurrentUser,
    os_type: str | None = None,
    phase: str | None = None,
    status: str | None = None,
    server_id: str | None = None,
    wave: str | None = None,
) -> dict[str, object]:
    _ = user
    payload = dashboard(
        session,
        os_type=os_type,
        phase=phase,
        status=status,
        server_id=server_id,
        wave=wave,
    )
    runs = payload["recent_runs"]
    payload["recent_runs"] = [HealthCheckRead.model_validate(run).model_dump(mode="json") for run in runs]
    return payload
