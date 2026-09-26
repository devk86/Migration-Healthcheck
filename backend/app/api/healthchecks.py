import uuid

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, Writer
from app.errors import NotFoundError
from app.models import HealthCheckResult, HealthCheckRun
from app.schemas.healthcheck import HealthCheckCreate, HealthCheckRead, HealthCheckResultRead
from app.services.healthcheck_service import cancel_run, create_run

router = APIRouter(prefix="/healthchecks", tags=["healthchecks"])


@router.post("", response_model=HealthCheckRead, status_code=201)
def start_healthcheck(payload: HealthCheckCreate, session: DbSession, user: Writer) -> HealthCheckRead:
    run = create_run(
        session,
        server_ids=payload.server_ids,
        phase=payload.phase,
        actor=user.username,
        user_id=user.id,
    )
    return HealthCheckRead.model_validate(run)


@router.get("", response_model=list[HealthCheckRead])
def list_healthchecks(
    session: DbSession,
    user: CurrentUser,
    phase: str | None = None,
    status: str | None = None,
) -> list[HealthCheckRead]:
    _ = user
    stmt = select(HealthCheckRun).order_by(HealthCheckRun.created_at.desc())
    if phase:
        stmt = stmt.where(HealthCheckRun.phase == phase)
    if status:
        stmt = stmt.where(HealthCheckRun.status == status)
    return [HealthCheckRead.model_validate(row) for row in session.scalars(stmt)]


@router.get("/{run_id}", response_model=HealthCheckRead)
def get_healthcheck(run_id: uuid.UUID, session: DbSession, user: CurrentUser) -> HealthCheckRead:
    _ = user
    run = session.get(HealthCheckRun, run_id)
    if run is None:
        raise NotFoundError("Health check was not found.")
    return HealthCheckRead.model_validate(run)


@router.post("/{run_id}/cancel", response_model=HealthCheckRead)
def cancel_healthcheck(run_id: uuid.UUID, session: DbSession, user: Writer) -> HealthCheckRead:
    return HealthCheckRead.model_validate(cancel_run(session, run_id, user.username))


@router.get("/{run_id}/results", response_model=list[HealthCheckResultRead])
def healthcheck_results(run_id: uuid.UUID, session: DbSession, user: CurrentUser) -> list[HealthCheckResultRead]:
    _ = user
    if session.get(HealthCheckRun, run_id) is None:
        raise NotFoundError("Health check was not found.")
    rows = session.scalars(select(HealthCheckResult).where(HealthCheckResult.run_id == run_id))
    return [HealthCheckResultRead.model_validate(row) for row in rows]
