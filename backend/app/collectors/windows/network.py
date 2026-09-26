import json
from typing import Any


def parse_network(text: str) -> dict[str, object]:
    interfaces: list[dict[str, object]] = []
    gateway = ""
    dns: list[str] = []
    routes: list[str] = []
    ports: list[int] = []
    rows = _rows(text)
    if text.strip():
        loaded = json.loads(text)
        if isinstance(loaded, dict) and "adapters" in loaded:
            rows = _as_rows(loaded.get("adapters"))
            for route in _as_rows(loaded.get("routes")):
                destination = _text(route.get("DestinationPrefix"))
                hop = _text(route.get("NextHop"))
                routes.append(f"{destination} via {hop}".strip())
            for item in _as_list(loaded.get("ports")):
                value = item.get("LocalPort") if isinstance(item, dict) else item
                try:
                    ports.append(int(value))
                except (TypeError, ValueError):
                    continue
    for row in rows:
        addresses = [item for item in _list(row.get("IPAddress")) if _is_ipv4(item)]
        interfaces.append(
            {
                "name": _text(row.get("Description")),
                "addresses": addresses,
                "mac": _text(row.get("MACAddress")),
            }
        )
        if not gateway:
            gateways = _list(row.get("DefaultIPGateway"))
            gateway = gateways[0] if gateways else ""
        for server in _list(row.get("DNSServerSearchOrder")):
            if server not in dns:
                dns.append(server)
    return {
        "interfaces": interfaces,
        "gateway": gateway,
        "dns": dns,
        "routes": routes,
        "listening_ports": ports,
    }


def _as_rows(value: object) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _rows(text: str) -> list[dict[str, Any]]:
    if not text.strip():
        return []
    loaded = json.loads(text)
    if isinstance(loaded, dict):
        return [loaded]
    if isinstance(loaded, list):
        return [item for item in loaded if isinstance(item, dict)]
    return []


def _list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str) and value:
        return [value]
    return []


def _is_ipv4(value: str) -> bool:
    parts = value.split(".")
    return len(parts) == 4 and all(part.isdigit() for part in parts)


def _text(value: object) -> str:
    return "" if value is None else str(value)
