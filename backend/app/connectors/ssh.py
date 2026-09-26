import asyncio
from typing import Any

from app.collectors.linux.commands import ALLOWED, HOSTNAME
from app.connectors.base import BaseConnector, CommandResult, ConnectionTestResult
from app.errors import AuthenticationFailed, CommandFailed, ConnectionFailed, TimeoutFailed


class SSHConnector(BaseConnector):
    def __init__(
        self,
        host: str,
        username: str,
        password: str | None = None,
        private_key: str | None = None,
        port: int = 22,
        connect_timeout: int = 10,
        command_timeout: int = 60,
    ) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.private_key = private_key
        self.connect_timeout = connect_timeout
        self.command_timeout = command_timeout
        self._client: Any = None

    async def connect(self) -> None:
        await asyncio.to_thread(self._connect)

    def _connect(self) -> None:
        import io

        import paramiko

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pkey = None
        if self.private_key:
            pkey = paramiko.RSAKey.from_private_key(io.StringIO(self.private_key))
        try:
            client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                pkey=pkey,
                timeout=self.connect_timeout,
                banner_timeout=self.connect_timeout,
                auth_timeout=self.connect_timeout,
                look_for_keys=False,
                allow_agent=False,
            )
        except paramiko.AuthenticationException as exc:
            raise AuthenticationFailed("Authentication failed.") from exc
        except TimeoutError as exc:
            raise TimeoutFailed("Connection timed out.") from exc
        except (OSError, paramiko.SSHException) as exc:
            raise ConnectionFailed("Server is unreachable.") from exc
        self._client = client

    async def execute(self, command: str) -> CommandResult:
        if command not in ALLOWED:
            raise CommandFailed("Command is not allowed.")
        return await asyncio.to_thread(self._execute, command)

    def _execute(self, command: str) -> CommandResult:
        if self._client is None:
            self._connect()
        try:
            _stdin, stdout, stderr = self._client.exec_command(command, timeout=self.command_timeout)
            exit_code = int(stdout.channel.recv_exit_status())
            result = CommandResult(
                command=command,
                stdout=stdout.read().decode(errors="replace"),
                stderr=stderr.read().decode(errors="replace"),
                exit_code=exit_code,
            )
        except TimeoutError as exc:
            raise TimeoutFailed("Command timed out.") from exc
        return self._record(result)

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    async def test_connection(self) -> ConnectionTestResult:
        try:
            await self.connect()
            result = await self.execute(HOSTNAME)
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
