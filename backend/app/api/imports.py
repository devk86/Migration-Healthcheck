from fastapi import APIRouter, File, Form, UploadFile

from app.api.deps import DbSession, Writer
from app.config import get_settings
from app.errors import ValidationFailed
from app.schemas.server import ImportResult
from app.services.import_service import import_servers

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/servers", response_model=ImportResult)
async def import_server_csv(
    session: DbSession,
    user: Writer,
    file: UploadFile = File(...),
    mode: str = Form("preview"),
) -> ImportResult:
    content = await file.read()
    if len(content) > get_settings().max_upload_bytes:
        raise ValidationFailed("CSV file is too large.")
    filename = (file.filename or "").lower()
    if filename and not filename.endswith(".csv"):
        raise ValidationFailed("Upload a CSV file.")
    result = import_servers(session, content, mode=mode, actor=user.username)
    return ImportResult.model_validate(result)
