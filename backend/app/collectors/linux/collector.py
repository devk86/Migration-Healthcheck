from typing import Any

from app.collectors.linux import commands as cmd
from app.collectors.linux.cpu import parse_cpuinfo, parse_loadavg, parse_usage
from app.collectors.linux.disk import parse_disk
from app.collectors.linux.memory import parse_memory
from app.collectors.linux.network import (
    build_interfaces,
    parse_addresses,
    parse_dns,
    parse_gateway,
    parse_links,
    parse_ports,
    parse_routes,
)
from app.collectors.linux.os import parse_os_release, parse_timezone, parse_uptime
from app.collectors.linux.packages import parse_packages
from app.collectors.linux.processes import parse_processes
from app.collectors.linux.services import (
    merge_enabled,
    parse_enabled,
    parse_service_status_all,
    parse_systemctl_units,
)
from app.connectors.base import BaseConnector, CommandResult


class LinuxCollector:
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
            snapshot["cpu"] = await self._cpu()
        if "memory" in self.checks:
            snapshot["memory"] = await self._section("memory", cmd.MEMORY, parse_memory)
        if "disk" in self.checks:
            snapshot["disk"] = await self._section("disk", cmd.DISK, parse_disk)
        if "network" in self.checks:
            snapshot["network"] = await self._network()
        if "services" in self.checks:
            snapshot["services"] = {"items": await self._services()}
        if "processes" in self.checks:
            snapshot["processes"] = await self._section("processes", cmd.PROCESSES, parse_processes)
        if "software" in self.checks:
            snapshot["software"] = await self._section("software", cmd.PACKAGES, parse_packages)
        return snapshot

    async def _run(self, category: str, command: str) -> CommandResult | None:
        try:
            result = await self.connector.execute(command)
        except Exception as exc:
            self.errors.append({"category": category, "code": getattr(exc, "code", "COLLECTOR_ERROR")})
            return None
        if result.exit_code != 0 and not result.stdout.strip():
            self.errors.append({"category": category, "code": "COMMAND_ERROR"})
            return None
        return result

    async def _section(self, category: str, command: str, parser: Any) -> Any:
        result = await self._run(category, command)
        if result is None:
            return {}
        try:
            return parser(result.stdout)
        except Exception:
            self.errors.append({"category": category, "code": "PARSER_ERROR"})
            return {}

    async def _os(self) -> dict[str, Any]:
        hostname = await self._run("os", cmd.HOSTNAME)
        release = await self._run("os", cmd.OS_RELEASE)
        kernel = await self._run("os", cmd.KERNEL)
        arch = await self._run("os", cmd.ARCH)
        uptime = await self._run("os", cmd.UPTIME)
        timezone = await self._run("os", cmd.TIMEZONE)
        if timezone is None:
            timezone = await self._run("os", cmd.TIMEZONE_FALLBACK)
        parsed = parse_os_release(release.stdout if release else "")
        return {
            "hostname": (hostname.stdout.strip() if hostname else ""),
            "distribution": parsed["distribution"],
            "distribution_version": parsed["distribution_version"],
            "kernel": kernel.stdout.strip() if kernel else "",
            "architecture": arch.stdout.strip() if arch else "",
            "uptime_seconds": parse_uptime(uptime.stdout) if uptime else None,
            "timezone": parse_timezone(timezone.stdout) if timezone else "",
        }

    async def _cpu(self) -> dict[str, Any]:
        info = await self._section("cpu", cmd.CPUINFO, parse_cpuinfo)
        load = await self._section("cpu", cmd.LOADAVG, parse_loadavg)
        usage = await self._section("cpu", cmd.CPU_USAGE, parse_usage)
        if not isinstance(info, dict):
            info = {}
        if not isinstance(load, dict):
            load = {}
        info.update(load)
        info["usage_percent"] = usage if isinstance(usage, float) else None
        info["architecture"] = ""
        arch = await self._run("cpu", cmd.ARCH)
        if arch:
            info["architecture"] = arch.stdout.strip()
        return info

    async def _network(self) -> dict[str, Any]:
        addresses = await self._section("network", cmd.NET_ADDR, parse_addresses)
        links = await self._section("network", cmd.NET_LINK, parse_links)
        gateway = await self._section("network", cmd.NET_ROUTE, parse_gateway)
        dns = await self._section("network", cmd.NET_DNS, parse_dns)
        routes = await self._section("network", cmd.NET_ROUTE, parse_routes)
        ports = await self._section("network", cmd.NET_LISTEN, parse_ports)
        if not isinstance(addresses, dict):
            addresses = {}
        if not isinstance(links, dict):
            links = {}
        return {
            "interfaces": build_interfaces(addresses, links),
            "gateway": gateway if isinstance(gateway, str) else "",
            "dns": dns if isinstance(dns, list) else [],
            "routes": routes if isinstance(routes, list) else [],
            "listening_ports": ports if isinstance(ports, list) else [],
        }

    async def _services(self) -> list[dict[str, object]]:
        units = await self._run("services", cmd.SERVICES)
        enabled = await self._run("services", cmd.SERVICE_ENABLED)
        if units is None:
            fallback = await self._run("services", cmd.SERVICES_FALLBACK)
            if fallback is None:
                return []
            try:
                return parse_service_status_all(fallback.stdout)
            except Exception:
                self.errors.append({"category": "services", "code": "PARSER_ERROR"})
                return []
        try:
            items = parse_systemctl_units(units.stdout)
            enabled_map = parse_enabled(enabled.stdout) if enabled else {}
            return merge_enabled(items, enabled_map)
        except Exception:
            self.errors.append({"category": "services", "code": "PARSER_ERROR"})
            return []
