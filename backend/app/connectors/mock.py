from app.collectors.mock_data import stdout_for
from app.connectors.base import BaseConnector, CommandResult, ConnectionTestResult


class MockConnector(BaseConnector):
    def __init__(self, os_type: str, name: str, phase: str) -> None:
        super().__init__()
        self.os_type = os_type
        self.name = name
        self.phase = phase
        self.connected = False

    async def connect(self) -> None:
        self.connected = True

    async def execute(self, command: str) -> CommandResult:
        stdout, exit_code = stdout_for(self.os_type, self.name, self.phase, command)
        return self._record(CommandResult(command=command, stdout=stdout, stderr="", exit_code=exit_code))

    async def close(self) -> None:
        self.connected = False

    async def test_connection(self) -> ConnectionTestResult:
        await self.connect()
        await self.close()
        return ConnectionTestResult(True, "OK", "Mock connection succeeded.")
