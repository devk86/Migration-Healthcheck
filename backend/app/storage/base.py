from abc import ABC, abstractmethod
from typing import Any


class SnapshotStorage(ABC):
    @abstractmethod
    async def save(
        self,
        phase: str,
        server_id: str,
        run_id: str,
        normalized: dict[str, Any],
        raw: dict[str, Any],
    ) -> tuple[str, str, str]:
        """Return normalized path, raw path, and sha256 checksum."""

    @abstractmethod
    async def load(self, path: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def delete(self, path: str) -> None:
        ...


class LogStorage(ABC):
    @abstractmethod
    async def save(
        self,
        phase: str,
        server_id: str,
        run_id: str,
        collector: str,
        connection: str,
        commands: list[dict[str, Any]],
    ) -> str:
        ...

    @abstractmethod
    async def load(self, directory: str) -> dict[str, Any]:
        ...


class CredentialProvider(ABC):
    @abstractmethod
    async def get_secret(self, server_id: str, kind: str) -> str | None:
        ...

    @abstractmethod
    async def put_secret(self, server_id: str, kind: str, username: str, secret: str) -> None:
        ...
