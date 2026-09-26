from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Comparison, ComparisonResult, HealthCheckResult, HealthCheckRun, Server


def dashboard(
    session: Session,
    *,
    os_type: str | None = None,
    phase: str | None = None,
    status: str | None = None,
    server_id: str | None = None,
    wave: str | None = None,
) -> dict[str, Any]:
    servers = select(Server.id)
    if os_type:
        servers = servers.where(Server.os_type == os_type.lower())
    if wave:
        servers = servers.where(Server.wave == wave)
    if server_id:
        servers = servers.where(Server.id == server_id)
    server_ids = list(session.scalars(servers))
    total = len(server_ids)
    if not server_ids:
        return {
            "total_servers": 0,
            "pre_completed": 0,
            "post_completed": 0,
            "pass_count": 0,
            "warning_count": 0,
            "failure_count": 0,
            "connection_errors": 0,
            "os_distribution": [],
            "failures_by_category": [],
            "recent_runs": [],
        }
    pre_completed = session.scalar(
        select(func.count()).select_from(Server).where(Server.id.in_(server_ids), Server.last_pre_check.is_not(None))
    ) or 0
    post_completed = session.scalar(
        select(func.count()).select_from(Server).where(Server.id.in_(server_ids), Server.last_post_check.is_not(None))
    ) or 0
    comparisons = list(
        session.scalars(select(Comparison).where(Comparison.server_id.in_(server_ids)).order_by(Comparison.created_at.desc()))
    )
    if status:
        comparisons = [item for item in comparisons if item.overall_status == status]
    latest: dict[str, Comparison] = {}
    for item in comparisons:
        key = str(item.server_id)
        if key not in latest:
            latest[key] = item
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for item in latest.values():
        if item.overall_status in counts:
            counts[item.overall_status] += 1
    connection_errors = session.scalar(
        select(func.count())
        .select_from(HealthCheckResult)
        .where(HealthCheckResult.server_id.in_(server_ids), HealthCheckResult.error_code == "CONNECTION_ERROR")
    ) or 0
    runs = select(HealthCheckRun).order_by(HealthCheckRun.created_at.desc()).limit(8)
    if phase:
        runs = runs.where(HealthCheckRun.phase == phase)
    recent = list(session.scalars(runs))
    os_rows = session.execute(select(Server.os_type, func.count()).group_by(Server.os_type)).all()
    failure_rows = session.execute(
        select(ComparisonResult.category, func.count())
        .where(ComparisonResult.status == "FAIL")
        .group_by(ComparisonResult.category)
    ).all()
    return {
        "total_servers": total,
        "pre_completed": int(pre_completed),
        "post_completed": int(post_completed),
        "pass_count": counts["PASS"],
        "warning_count": counts["WARN"],
        "failure_count": counts["FAIL"],
        "connection_errors": int(connection_errors),
        "os_distribution": [{"os_type": row[0], "count": row[1]} for row in os_rows],
        "failures_by_category": [{"category": row[0], "count": row[1]} for row in failure_rows],
        "recent_runs": recent,
    }
