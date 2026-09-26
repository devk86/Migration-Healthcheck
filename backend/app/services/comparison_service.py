import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.comparison.engine import compare
from app.config import get_settings
from app.errors import NotFoundError, ValidationFailed
from app.models import Comparison, ComparisonResult, Snapshot
from app.services.audit import record
from app.storage.local import snapshot_storage
from app.utils.filesystem import safe_path


async def create_comparison(
    session: Session,
    *,
    pre_snapshot_id: uuid.UUID,
    post_snapshot_id: uuid.UUID,
    actor: str,
    user_id: uuid.UUID | None,
) -> Comparison:
    pre = session.get(Snapshot, pre_snapshot_id)
    post = session.get(Snapshot, post_snapshot_id)
    if pre is None or post is None:
        raise NotFoundError("Snapshot was not found.")
    if pre.server_id != post.server_id:
        raise ValidationFailed("Snapshots must belong to the same server.")
    if pre.phase != "PRE" or post.phase != "POST":
        raise ValidationFailed("Choose a PRE snapshot and a POST snapshot.")
    storage = snapshot_storage()
    pre_body = await storage.load(pre.path)
    post_body = await storage.load(post.path)
    outcome = compare(pre_body, post_body)
    comparison = Comparison(
        server_id=pre.server_id,
        pre_snapshot_id=pre.id,
        post_snapshot_id=post.id,
        overall_status=str(outcome["overall_status"]),
        created_by=user_id,
    )
    session.add(comparison)
    session.flush()
    categories = outcome["categories"]
    if isinstance(categories, list):
        for row in categories:
            if not isinstance(row, dict):
                continue
            session.add(
                ComparisonResult(
                    comparison_id=comparison.id,
                    category=str(row["category"]),
                    metric=str(row["metric"]),
                    pre_value=str(row["pre_value"]),
                    post_value=str(row["post_value"]),
                    change=str(row["change"]),
                    status=str(row["status"]),
                    changed=bool(row["changed"]),
                )
            )
    _write_file(comparison.id, outcome)
    record(session, actor, "comparison.create", str(comparison.id))
    session.commit()
    session.refresh(comparison)
    return comparison


async def ensure_missing_comparisons(
    session: Session,
    *,
    actor: str = "system",
    user_id: uuid.UUID | None = None,
) -> None:
    latest: dict[tuple[uuid.UUID, str], uuid.UUID] = {}
    for snapshot in session.scalars(select(Snapshot).order_by(Snapshot.created_at.desc())):
        latest.setdefault((snapshot.server_id, snapshot.phase), snapshot.id)
    server_ids = {server_id for server_id, _phase in latest}
    for server_id in server_ids:
        pre_id = latest.get((server_id, "PRE"))
        post_id = latest.get((server_id, "POST"))
        if pre_id is None or post_id is None:
            continue
        existing = session.scalar(
            select(Comparison).where(
                Comparison.pre_snapshot_id == pre_id,
                Comparison.post_snapshot_id == post_id,
            )
        )
        if existing is not None:
            continue
        await create_comparison(
            session,
            pre_snapshot_id=pre_id,
            post_snapshot_id=post_id,
            actor=actor,
            user_id=user_id,
        )


def list_results(session: Session, comparison_id: uuid.UUID) -> list[ComparisonResult]:
    return list(
        session.scalars(
            select(ComparisonResult)
            .where(ComparisonResult.comparison_id == comparison_id)
            .order_by(ComparisonResult.category, ComparisonResult.metric)
        )
    )


def _write_file(comparison_id: uuid.UUID, outcome: dict[str, Any]) -> None:
    root = Path(get_settings().data_dir) / "comparisons"
    root.mkdir(parents=True, exist_ok=True)
    path = safe_path(root, f"{comparison_id}.json")
    path.write_text(json.dumps(outcome, indent=2), encoding="utf-8")
