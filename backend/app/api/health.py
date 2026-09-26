import asyncio
import logging
from typing import Literal

import psycopg
from fastapi import APIRouter, Response
from pydantic import BaseModel
from redis import Redis

from app.config import get_settings
from app.errors import ConnectionCheckError

logger = logging.getLogger(__name__)

router = APIRouter()

CheckStatus = Literal["ok", "error"]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: str
    version: str
    environment: str
    checks: dict[str, CheckStatus]


def probe_database() -> CheckStatus:
    settings = get_settings()
    try:
        with psycopg.connect(settings.psycopg_url, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
    except Exception as exc:
        logger.warning(
            "database probe failed",
            extra={"error_type": type(exc).__name__, "code": ConnectionCheckError.code},
        )
        return "error"
    return "ok"


def probe_redis() -> CheckStatus:
    settings = get_settings()
    client: Redis | None = None
    try:
        client = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        client.ping()
    except Exception as exc:
        logger.warning(
            "redis probe failed",
            extra={"error_type": type(exc).__name__, "code": ConnectionCheckError.code},
        )
        return "error"
    finally:
        if client is not None:
            client.close()
    return "ok"


@router.get("/health", response_model=HealthResponse)
async def health(response: Response) -> HealthResponse:
    settings = get_settings()
    database, redis = await asyncio.gather(
        asyncio.to_thread(probe_database),
        asyncio.to_thread(probe_redis),
    )
    checks: dict[str, CheckStatus] = {
        "database": database,
        "redis": redis,
    }
    healthy = all(value == "ok" for value in checks.values())
    status: Literal["ok", "degraded"] = "ok" if healthy else "degraded"
    if status != "ok":
        response.status_code = 503
    return HealthResponse(
        status=status,
        service="migration-healthcheck",
        version=settings.app_version,
        environment=settings.app_env,
        checks=checks,
    )
