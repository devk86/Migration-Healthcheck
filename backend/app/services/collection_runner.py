import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.collectors.registry import ALL_CHECKS, get_collector
from app.config import get_settings
from app.connectors.mock import MockConnector
from app.connectors.ssh import SSHConnector
from app.connectors.winrm import WinRMConnector
from app.errors import AppError
from app.models import HealthCheckResult, Server, Snapshot
from app.security.crypto import decrypt_secret
from app.services.credential_service import resolve_credential
from app.storage.local import log_storage, snapshot_storage


async def collect_server(session: Session, run_id: uuid.UUID, server_id: uuid.UUID, phase: str) -> bool:
    server = session.get(Server, server_id)
    if server is None or not server.enabled:
        _result(session, run_id, server_id, "FAILED", "NOT_FOUND", "Server was not found.")
        return False
    credential = resolve_credential(session, server)
    if credential is None:
        _result(session, run_id, server.id, "FAILED", "AUTHENTICATION_ERROR", "Credential is required.")
        return False
    try:
        secret = decrypt_secret(credential.secret_encrypted)
    except AppError:
        _result(session, run_id, server.id, "FAILED", "STORAGE_ERROR", "Credential could not be read.")
        return False
    connector = _connector(server, credential.username, secret, credential.kind, phase)
    settings = get_settings()
    try:
        await connector.connect()
        collector = get_collector(server.os_type, connector, ALL_CHECKS)
        sections = await collector.collect()
        collected_at = datetime.now(UTC).isoformat()
        snapshot = {
            "schema_version": "1.0",
            "server": {
                "id": str(server.id),
                "name": server.name,
                "address": server.address,
                "os_type": server.os_type,
            },
            "collection": {
                "phase": phase,
                "run_id": str(run_id),
                "collected_at": collected_at,
                "errors": collector.errors,
            },
            **sections,
        }
        raw = {"commands": [item.as_dict() for item in connector.history]}
        normalized_path, raw_path, checksum = await snapshot_storage().save(
            phase.lower(),
            str(server.id),
            str(run_id),
            snapshot,
            raw,
        )
        log_path = await log_storage().save(
            phase.lower(),
            str(server.id),
            str(run_id),
            _collector_log(collector.errors),
            "connected\n",
            raw["commands"],
        )
        stored = Snapshot(
            server_id=server.id,
            run_id=run_id,
            phase=phase,
            path=normalized_path,
            raw_path=raw_path,
            log_path=log_path,
            checksum=checksum,
        )
        session.add(stored)
        session.flush()
        _result(session, run_id, server.id, "COMPLETED", None, None, stored.id)
        now = datetime.now(UTC)
        if phase == "PRE":
            server.last_pre_check = now
        else:
            server.last_post_check = now
        server.last_connection_status = "ok"
        server.last_connection_checked_at = now
        return True
    except AppError as exc:
        _result(session, run_id, server.id, "FAILED", exc.code, exc.args[0] if exc.args else exc.code)
        server.last_connection_status = exc.code
        server.last_connection_checked_at = datetime.now(UTC)
        return False
    finally:
        await connector.close()
        _ = settings


def _connector(server: Server, username: str, secret: str, kind: str, phase: str) -> Any:
    settings = get_settings()
    if settings.mock_connectors:
        return MockConnector(server.os_type, server.name, phase)
    if server.os_type == "windows":
        return WinRMConnector(
            host=server.address,
            username=username,
            password=secret,
            port=settings.winrm_port,
            transport=settings.winrm_transport,
            server_cert_validation=settings.winrm_server_cert_validation,
            timeout=settings.winrm_timeout,
        )
    return SSHConnector(
        host=server.address,
        port=settings.ssh_port,
        username=username,
        password=None if kind == "SSH_PRIVATE_KEY" else secret,
        private_key=secret if kind == "SSH_PRIVATE_KEY" else None,
        connect_timeout=settings.ssh_connect_timeout,
        command_timeout=settings.ssh_command_timeout,
    )


def _result(
    session: Session,
    run_id: uuid.UUID,
    server_id: uuid.UUID,
    status: str,
    code: str | None,
    message: str | None,
    snapshot_id: uuid.UUID | None = None,
) -> None:
    session.add(
        HealthCheckResult(
            run_id=run_id,
            server_id=server_id,
            status=status,
            error_code=code,
            message=message,
            snapshot_id=snapshot_id,
        )
    )


def _collector_log(errors: list[dict[str, str]]) -> str:
    if not errors:
        return "collection completed\n"
    return "".join(f"{item['category']} {item['code']}\n" for item in errors)
