import uuid

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, Writer
from app.errors import NotFoundError
from app.models import Comparison
from app.schemas.comparison import ComparisonCreate, ComparisonRead, ComparisonResultRead
from app.services.comparison_service import create_comparison, list_results

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


def _read(session: DbSession, comparison: Comparison) -> ComparisonRead:
    data = ComparisonRead.model_validate(comparison)
    data.results = [ComparisonResultRead.model_validate(row) for row in list_results(session, comparison.id)]
    return data


@router.post("", response_model=ComparisonRead, status_code=201)
async def create(payload: ComparisonCreate, session: DbSession, user: Writer) -> ComparisonRead:
    comparison = await create_comparison(
        session,
        pre_snapshot_id=payload.pre_snapshot_id,
        post_snapshot_id=payload.post_snapshot_id,
        actor=user.username,
        user_id=user.id,
    )
    return _read(session, comparison)


@router.get("", response_model=list[ComparisonRead])
def list_comparisons(session: DbSession, user: CurrentUser) -> list[ComparisonRead]:
    _ = user
    rows = session.scalars(select(Comparison).order_by(Comparison.created_at.desc()))
    return [_read(session, row) for row in rows]


@router.get("/{comparison_id}", response_model=ComparisonRead)
def get_comparison(comparison_id: uuid.UUID, session: DbSession, user: CurrentUser) -> ComparisonRead:
    _ = user
    comparison = session.get(Comparison, comparison_id)
    if comparison is None:
        raise NotFoundError("Comparison was not found.")
    return _read(session, comparison)
