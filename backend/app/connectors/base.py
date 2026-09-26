from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CommandResult:
    command: str
    stdout: str
    stderr: str
    exit_code: int

    def as_dict(self) -> dict[str, str | int]:
        return {
            "command": self.command,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
        }


@dataclass
class ConnectionTestResult:
    ok: bool
    code: str
    message: str


class BaseConnector(ABC):
    def __init__(self) -> None:
        self.history: list[CommandResult] = []

    @abstractmethod
    async def connect(self) -> None:
        ...

    @abstractmethod
    async def execute(self, command: str) -> CommandResult:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...

    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult:
        ...

    def _record(self, result: CommandResult) -> CommandResult:
        self.history.append(result)
        return result
