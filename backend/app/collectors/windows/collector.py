from typing import Any

from app.collectors.windows import commands as cmd
from app.collectors.windows.cpu import parse_cpu
from app.collectors.windows.disk import parse_disk
from app.collectors.windows.memory import parse_memory
from app.collectors.windows.network import parse_network
from app.collectors.windows.os import parse_os, parse_timezone
from app.collectors.windows.processes import parse_processes
from app.collectors.windows.services import parse_services
from app.collectors.windows.software import parse_software
from app.connectors.base import BaseConnector


class WindowsCollector:
    def __init__(self, connector: BaseConnector, checks: list[str]) -> None:
        self.connector = connector
        self.checks = set(checks)
        self.errors: list[dict[str, str]] = []

    async def collect(self) -> dict[str, Any]:
        snapshot: dict[str, Any] = {
            "os": {},
            "cpu": {},
            "memory": {},
            "disk": {"volumes": []},
            "network": {},
            "services": {"items": []},
            "processes": {"items": []},
            "software": {},
        }
        if "os" in self.checks:
            snapshot["os"] = await self._os()
        if "cpu" in self.checks:
            snapshot["cpu"] = await self._parse("cpu", cmd.CPU, parse_cpu)
        if "memory" in self.checks:
            snapshot["memory"] = await self._parse("memory", cmd.MEMORY, parse_memory)
        if "disk" in self.checks:
            snapshot["disk"] = await self._parse("disk", cmd.DISK, parse_disk)
        if "network" in self.checks:
            snapshot["network"] = await self._parse("network", cmd.NETWORK, parse_network)
        if "services" in self.checks:
            snapshot["services"] = await self._parse("services", cmd.SERVICES, parse_services)
        if "processes" in self.checks:
            snapshot["processes"] = await self._parse("processes", cmd.PROCESSES, parse_processes)
        if "software" in self.checks:
            snapshot["software"] = await self._parse("software", cmd.SOFTWARE, parse_software)
        return snapshot

    async def _parse(self, category: str, command: str, parser: Any) -> Any:
        try:
            result = await self.connector.execute(command)
        except Exception as exc:
            self.errors.append({"category": category, "code": getattr(exc, "code", "COLLECTOR_ERROR")})
            return {}
        if result.exit_code != 0 and not result.stdout.strip():
            self.errors.append({"category": category, "code": "COMMAND_ERROR"})
            return {}
        try:
            return parser(result.stdout)
        except Exception:
            self.errors.append({"category": category, "code": "PARSER_ERROR"})
            return {}

    async def _os(self) -> dict[str, Any]:
        parsed = await self._parse("os", cmd.OS, parse_os)
        if not isinstance(parsed, dict):
            parsed = {}
        timezone = await self._parse("os", cmd.TIMEZONE, parse_timezone)
        parsed["timezone"] = timezone if isinstance(timezone, str) else ""
        return parsed
