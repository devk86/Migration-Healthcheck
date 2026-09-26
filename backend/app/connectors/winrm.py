import asyncio
from typing import Any

from app.collectors.windows.commands import ALLOWED, TIMEZONE
from app.connectors.base import BaseConnector, CommandResult, ConnectionTestResult
from app.errors import AuthenticationFailed, CommandFailed, ConnectionFailed, TimeoutFailed


class WinRMConnector(BaseConnector):
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 5985,
        transport: str = "ntlm",
        server_cert_validation: str = "ignore",
        timeout: int = 30,
    ) -> None:
        super().__init__()
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.transport = transport
        self.server_cert_validation = server_cert_validation
        self.timeout = timeout
        self._session: Any = None

    async def connect(self) -> None:
        await asyncio.to_thread(self._connect)

    def _connect(self) -> None:
        import winrm

        scheme = "https" if self.port == 5986 else "http"
        endpoint = f"{scheme}://{self.host}:{self.port}/wsman"
        try:
            self._session = winrm.Session(
                endpoint,
                auth=(self.username, self.password),
                transport=self.transport,
                server_cert_validation=self.server_cert_validation,
                operation_timeout_sec=self.timeout,
                read_timeout_sec=self.timeout + 5,
            )
        except Exception as exc:
            raise ConnectionFailed("Server is unreachable.") from exc

    async def execute(self, command: str) -> CommandResult:
        if command not in ALLOWED:
            raise CommandFailed("Command is not allowed.")
        return await asyncio.to_thread(self._execute, command)

    def _execute(self, command: str) -> CommandResult:
        if self._session is None:
            self._connect()
        try:
            completed = self._session.run_ps(command)
        except Exception as exc:
            message = str(exc).lower()
            if "auth" in message or "401" in message or "credentials" in message:
                raise AuthenticationFailed("Authentication failed.") from exc
            if "timed out" in message or "timeout" in message:
                raise TimeoutFailed("Command timed out.") from exc
            raise ConnectionFailed("Server is unreachable.") from exc
        stdout = _decode(completed.std_out)
        stderr = _decode(completed.std_err)
        return self._record(
            CommandResult(
                command=command,
                stdout=stdout,
                stderr=stderr,
                exit_code=int(completed.status_code),
            )
        )

    async def close(self) -> None:
        self._session = None

    async def test_connection(self) -> ConnectionTestResult:
        try:
            await self.connect()
            result = await self.execute(TIMEZONE)
            await self.close()
        except AuthenticationFailed:
            return ConnectionTestResult(False, "AUTHENTICATION_ERROR", "Authentication failed.")
        except TimeoutFailed:
            return ConnectionTestResult(False, "TIMEOUT", "Connection timed out.")
        except ConnectionFailed:
            return ConnectionTestResult(False, "CONNECTION_ERROR", "Server is unreachable.")
        if result.exit_code != 0:
            return ConnectionTestResult(False, "COMMAND_ERROR", "Connection test command failed.")
        return ConnectionTestResult(True, "OK", "Connected.")


def _decode(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value or "")
