import hashlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import NotFoundError, StorageFailed
from app.models import Credential, GlobalCredential, Server
from app.security.crypto import decrypt_secret, encrypt_secret
from app.storage.base import CredentialProvider, LogStorage, SnapshotStorage
from app.utils.filesystem import safe_path


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=str)


class LocalSnapshotStorage(SnapshotStorage):
    def __init__(self, data_dir: str) -> None:
        self.root = Path(data_dir) / "snapshots"

    async def save(
        self,
        phase: str,
        server_id: str,
        run_id: str,
        normalized: dict[str, Any],
        raw: dict[str, Any],
    ) -> tuple[str, str, str]:
        directory = safe_path(self.root, phase, server_id)
        directory.mkdir(parents=True, exist_ok=True)
        normalized_path = safe_path(self.root, phase, server_id, f"{run_id}.json")
        raw_path = safe_path(self.root, phase, server_id, f"{run_id}.raw.json")
        if normalized_path.exists():
            raise StorageFailed("Snapshot already exists and cannot be changed.")
        body = _dump(normalized)
        normalized_path.write_text(body, encoding="utf-8")
        raw_path.write_text(_dump(raw), encoding="utf-8")
        checksum = hashlib.sha256(body.encode()).hexdigest()
        return str(normalized_path), str(raw_path), checksum

    async def load(self, path: str) -> dict[str, Any]:
        candidate = Path(path).resolve()
        root = self.root.resolve()
        if not candidate.is_relative_to(root) or not candidate.is_file():
            raise NotFoundError("Snapshot file was not found.")
        loaded: dict[str, Any] = json.loads(candidate.read_text(encoding="utf-8"))
        return loaded

    async def delete(self, path: str) -> None:
        candidate = Path(path).resolve()
        root = self.root.resolve()
        if not candidate.is_relative_to(root):
            raise StorageFailed("Path is not allowed.")
        if candidate.is_file():
            candidate.unlink()


class LocalLogStorage(LogStorage):
    def __init__(self, data_dir: str) -> None:
        self.root = Path(data_dir) / "logs"

    async def save(
        self,
        phase: str,
        server_id: str,
        run_id: str,
        collector: str,
        connection: str,
        commands: list[dict[str, Any]],
    ) -> str:
        directory = safe_path(self.root, phase, server_id, run_id)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "collector.log").write_text(collector, encoding="utf-8")
        (directory / "connection.log").write_text(connection, encoding="utf-8")
        (directory / "commands.json").write_text(_dump({"commands": commands}), encoding="utf-8")
        return str(directory)

    async def load(self, directory: str) -> dict[str, Any]:
        folder = Path(directory).resolve()
        root = self.root.resolve()
        if not folder.is_relative_to(root) or not folder.is_dir():
            raise NotFoundError("Log folder was not found.")
        commands_file = folder / "commands.json"
        commands: list[dict[str, Any]] = []
        if commands_file.is_file():
            payload = json.loads(commands_file.read_text(encoding="utf-8"))
            raw_commands = payload.get("commands", [])
            if isinstance(raw_commands, list):
                commands = [item for item in raw_commands if isinstance(item, dict)]
        return {
            "collector": (folder / "collector.log").read_text(encoding="utf-8")
            if (folder / "collector.log").is_file()
            else "",
            "connection": (folder / "connection.log").read_text(encoding="utf-8")
            if (folder / "connection.log").is_file()
            else "",
            "commands": commands,
        }


class LocalCredentialProvider(CredentialProvider):
    def __init__(self, session: Session) -> None:
        self.session = session

    async def get_secret(self, server_id: str, kind: str) -> str | None:
        credential = self.session.scalar(
            select(Credential).where(Credential.server_id == server_id, Credential.kind == kind)
        )
        if credential is None:
            server = self.session.get(Server, server_id)
            if server is None:
                return None
            credential = self.session.scalar(
                select(GlobalCredential).where(
                    GlobalCredential.os_type == server.os_type,
                    GlobalCredential.kind == kind,
                )
            )
        if credential is None:
            return None
        return decrypt_secret(credential.secret_encrypted)

    async def put_secret(self, server_id: str, kind: str, username: str, secret: str) -> None:
        credential = self.session.scalar(
            select(Credential).where(Credential.server_id == server_id, Credential.kind == kind)
        )
        encrypted = encrypt_secret(secret)
        if credential is None:
            self.session.add(
                Credential(
                    server_id=server_id,
                    kind=kind,
                    username=username,
                    secret_encrypted=encrypted,
                )
            )
        else:
            credential.username = username
            credential.secret_encrypted = encrypted
        self.session.commit()


class AzureBlobSnapshotStorage(SnapshotStorage):
    """Placeholder for a later Azure Blob implementation."""

    async def save(
        self,
        phase: str,
        server_id: str,
        run_id: str,
        normalized: dict[str, Any],
        raw: dict[str, Any],
    ) -> tuple[str, str, str]:
        raise NotImplementedError("Azure Blob snapshot storage is not configured.")

    async def load(self, path: str) -> dict[str, Any]:
        raise NotImplementedError("Azure Blob snapshot storage is not configured.")

    async def delete(self, path: str) -> None:
        raise NotImplementedError("Azure Blob snapshot storage is not configured.")


class AzureBlobLogStorage(LogStorage):
    async def save(
        self,
        phase: str,
        server_id: str,
        run_id: str,
        collector: str,
        connection: str,
        commands: list[dict[str, Any]],
    ) -> str:
        raise NotImplementedError("Azure Blob log storage is not configured.")

    async def load(self, directory: str) -> dict[str, Any]:
        raise NotImplementedError("Azure Blob log storage is not configured.")


class AzureKeyVaultCredentialProvider(CredentialProvider):
    async def get_secret(self, server_id: str, kind: str) -> str | None:
        raise NotImplementedError("Azure Key Vault is not configured.")

    async def put_secret(self, server_id: str, kind: str, username: str, secret: str) -> None:
        raise NotImplementedError("Azure Key Vault is not configured.")


def snapshot_storage() -> SnapshotStorage:
    from app.config import get_settings

    settings = get_settings()
    if settings.storage_backend == "azure":
        return AzureBlobSnapshotStorage()
    return LocalSnapshotStorage(settings.data_dir)


def log_storage() -> LogStorage:
    from app.config import get_settings

    settings = get_settings()
    if settings.storage_backend == "azure":
        return AzureBlobLogStorage()
    return LocalLogStorage(settings.data_dir)
