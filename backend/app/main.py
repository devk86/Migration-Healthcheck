import time
import uuid
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.auth import router as auth_router
from app.api.comparisons import router as comparisons_router
from app.api.credentials import global_router as global_credentials_router
from app.api.credentials import router as credentials_router
from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.healthchecks import router as healthchecks_router
from app.api.imports import router as imports_router
from app.api.logs import router as logs_router
from app.api.reports import router as reports_router
from app.api.servers import router as servers_router
from app.api.snapshots import router as snapshots_router
from app.config import get_settings
from app.errors import AppError
from app.utils.logging import configure_logging, request_id_var

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="Migration HealthCheck",
    version=__version__,
    summary="Pre- and post-migration health checks for Linux and Windows servers.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_hits: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def security_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_var.set(request_id)
    try:
        if get_settings().app_env != "test" and not _allow(request):
            response: Response = JSONResponse(
                status_code=429,
                content={"detail": {"code": "RATE_LIMIT", "message": "Too many requests."}},
            )
        else:
            response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.url.path not in {"/docs", "/redoc", "/openapi.json"} and not request.url.path.startswith("/docs"):
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response


def _allow(request: Request) -> bool:
    limit = 20 if request.url.path.endswith("/auth/login") else get_settings().rate_limit_per_minute
    now = time.monotonic()
    key = request.client.host if request.client else "unknown"
    bucket = _hits[key]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    message = str(exc) if exc.args else "The request could not be completed."
    return JSONResponse(status_code=exc.status_code, content={"detail": {"code": exc.code, "message": message}})


@app.exception_handler(RequestValidationError)
async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{"loc": list(error.get("loc", [])), "msg": error.get("msg", "")} for error in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"detail": {"code": "VALIDATION_ERROR", "message": "Request validation failed.", "errors": errors}},
    )


@app.exception_handler(Exception)
async def unhandled_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": {"code": "UNKNOWN_ERROR", "message": "The request could not be completed."}},
    )


for route in (
    health_router,
    auth_router,
    servers_router,
    credentials_router,
    global_credentials_router,
    imports_router,
    healthchecks_router,
    snapshots_router,
    logs_router,
    comparisons_router,
    reports_router,
    dashboard_router,
):
    app.include_router(route, prefix="/api/v1")
