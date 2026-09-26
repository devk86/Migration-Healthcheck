import asyncio
import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database.database import get_engine, get_sessionmaker
from app.errors import NotFoundError, ValidationFailed
from app.models import HealthCheckResult, HealthCheckRun, Server
from app.models.base import utcnow
from app.services.audit import record
from app.services.collection_runner import collect_server


def create_run(
    session: Session,
    *,
    server_ids: list[uuid.UUID],
    phase: str,
    actor: str,
    user_id: uuid.UUID | None,
    enqueue: bool = True,
) -> HealthCheckRun:
    if phase not in {"PRE", "POST"}:
        raise ValidationFailed("Phase must be PRE or POST.")
    if not server_ids:
        raise ValidationFailed("Select at least one server.")
    unique_ids = list(dict.fromkeys(server_ids))
    servers = [session.get(Server, server_id) for server_id in unique_ids]
    if any(server is None for server in servers):
        raise NotFoundError("One or more servers were not found.")
    if any(server is not None and not server.enabled for server in servers):
        raise ValidationFailed("Disabled servers cannot be checked.")
    run = HealthCheckRun(
        phase=phase,
        status="QUEUED",
        server_ids=[str(server_id) for server_id in unique_ids],
        created_by=user_id,
        total=len(unique_ids),
        queued_count=len(unique_ids),
    )
    session.add(run)
    record(session, actor, "healthcheck.create", f"{phase}:{len(unique_ids)}")
    session.commit()
    session.refresh(run)
    if enqueue:
        from app.workers.healthcheck_tasks import run_healthcheck

        run_healthcheck.delay(str(run.id))
        session.refresh(run)
    return run


def execute_run(run_id: str) -> None:
    session = get_sessionmaker()()
    try:
        run = session.get(HealthCheckRun, uuid.UUID(run_id))
        if run is None:
            return
        if run.cancel_requested:
            run.status = "CANCELLED"
            run.finished_at = utcnow()
            session.commit()
            return
        run.status = "RUNNING"
        run.started_at = utcnow()
        server_ids = list(run.server_ids)
        phase = run.phase
        session.commit()
    finally:
        session.close()

    sequential = get_engine().dialect.name == "sqlite" or len(server_ids) <= 1
    if sequential:
        for server_id in server_ids:
            if _cancelled(run_id):
                break
            _collect(run_id, server_id, phase)
    else:
        from concurrent.futures import ThreadPoolExecutor

        from app.config import get_settings

        workers = max(1, min(get_settings().celery_worker_concurrency, len(server_ids)))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = []
            for server_id in server_ids:
                if _cancelled(run_id):
                    break
                futures.append(pool.submit(_collect, run_id, server_id, phase))
            for future in futures:
                future.result()
    _finalize(run_id)


def cancel_run(session: Session, run_id: uuid.UUID, actor: str) -> HealthCheckRun:
    run = session.get(HealthCheckRun, run_id)
    if run is None:
        raise NotFoundError("Health check was not found.")
    run.cancel_requested = True
    if run.status in {"QUEUED", "RUNNING"}:
        run.status = "CANCELLED"
        run.finished_at = datetime.now(UTC)
    record(session, actor, "healthcheck.cancel", str(run.id))
    session.commit()
    session.refresh(run)
    return run


def _run_async(coro: object) -> object:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)  # type: ignore[arg-type]
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()  # type: ignore[arg-type]


def _collect(run_id: str, server_id: str, phase: str) -> None:
    session = get_sessionmaker()()
    try:
        ok = bool(
            _run_async(collect_server(session, uuid.UUID(run_id), uuid.UUID(server_id), phase))
        )
        changes: dict[str, object] = {"queued_count": HealthCheckRun.queued_count - 1}
        if ok:
            changes["completed"] = HealthCheckRun.completed + 1
        else:
            changes["failed_count"] = HealthCheckRun.failed_count + 1
        session.execute(update(HealthCheckRun).where(HealthCheckRun.id == uuid.UUID(run_id)).values(**changes))
        session.commit()
        if ok and phase == "POST":
            from app.services.comparison_service import ensure_missing_comparisons

            try:
                _run_async(ensure_missing_comparisons(session))
            except Exception:
                session.rollback()
    finally:
        session.close()


def _cancelled(run_id: str) -> bool:
    session = get_sessionmaker()()
    try:
        run = session.get(HealthCheckRun, uuid.UUID(run_id))
        return bool(run and run.cancel_requested)
    finally:
        session.close()


def _finalize(run_id: str) -> None:
    session = get_sessionmaker()()
    try:
        run = session.get(HealthCheckRun, uuid.UUID(run_id))
        if run is None or run.status == "CANCELLED":
            return
        results = list(session.scalars(select(HealthCheckResult).where(HealthCheckResult.run_id == run.id)))
        run.completed = sum(1 for item in results if item.status == "COMPLETED")
        run.failed_count = sum(1 for item in results if item.status != "COMPLETED")
        run.queued_count = max(run.total - len(results), 0)
        if run.cancel_requested:
            run.status = "CANCELLED"
        elif run.failed_count and run.completed:
            run.status = "PARTIAL"
        elif run.failed_count and not run.completed:
            run.status = "FAILED"
        else:
            run.status = "COMPLETED"
        run.running_count = 0
        run.finished_at = utcnow()
        session.commit()
    finally:
        session.close()
