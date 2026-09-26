import uuid

from fastapi import APIRouter
from fastapi.responses import FileResponse, HTMLResponse

from app.api.deps import CurrentUser, DbSession, Writer
from app.errors import NotFoundError
from app.models import Report
from app.schemas.comparison import ReportChoiceRead, ReportCreate, ReportRead
from app.services.comparison_service import ensure_missing_comparisons
from app.services.report_service import (
    create_report,
    html_document,
    list_report_choices,
    list_reports,
    report_file,
    snapshot_html_document,
)

router = APIRouter(prefix="/reports", tags=["reports"])

MEDIA = {
    "json": "application/json",
    "csv": "text/csv",
    "html": "text/html",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


@router.post("", response_model=ReportRead, status_code=201)
async def create(payload: ReportCreate, session: DbSession, user: Writer) -> ReportRead:
    report = await create_report(
        session,
        comparison_id=payload.comparison_id,
        report_format=payload.format,
        actor=user.username,
        user_id=user.id,
    )
    return ReportRead.model_validate(report)


@router.get("", response_model=list[ReportRead])
def list_all(session: DbSession, user: CurrentUser) -> list[ReportRead]:
    _ = user
    return [ReportRead.model_validate(row) for row in list_reports(session)]


@router.get("/choices", response_model=list[ReportChoiceRead])
async def report_choices(session: DbSession, user: CurrentUser) -> list[ReportChoiceRead]:
    _ = user
    await ensure_missing_comparisons(session, actor=user.username, user_id=user.id)
    return [ReportChoiceRead.model_validate(item) for item in list_report_choices(session)]


@router.get("/snapshots/{snapshot_id}/html")
async def download_snapshot_html(snapshot_id: uuid.UUID, session: DbSession, user: CurrentUser) -> HTMLResponse:
    _ = user
    filename, html = await snapshot_html_document(session, snapshot_id)
    return HTMLResponse(content=html, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/documents/{comparison_id}/{document}")
async def download_html_document(
    comparison_id: uuid.UUID,
    document: str,
    session: DbSession,
    user: CurrentUser,
) -> HTMLResponse:
    _ = user
    filename, html = await html_document(session, comparison_id, document)
    return HTMLResponse(content=html, headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/{report_id}", response_model=ReportRead)
def get_report(report_id: uuid.UUID, session: DbSession, user: CurrentUser) -> ReportRead:
    _ = user
    report = session.get(Report, report_id)
    if report is None:
        raise NotFoundError("Report was not found.")
    return ReportRead.model_validate(report)


@router.get("/{report_id}/download")
def download_report(report_id: uuid.UUID, session: DbSession, user: CurrentUser) -> FileResponse:
    _ = user
    report = session.get(Report, report_id)
    if report is None:
        raise NotFoundError("Report was not found.")
    path = report_file(report)
    return FileResponse(path, media_type=MEDIA.get(report.format, "application/octet-stream"), filename=path.name)
