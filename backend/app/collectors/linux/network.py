import re

_ADDR = re.compile(r"^\d+:\s+(\S+)\s+inet\s+(\d+\.\d+\.\d+\.\d+)")
_MAC = re.compile(r"^\d+:\s+(\S+?):?\s+.*link/ether\s+([0-9a-f:]{17})")
_PORT = re.compile(r":(\d+)(?:\s|$)")


def parse_addresses(text: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for line in text.splitlines():
        match = _ADDR.search(line.strip())
        if match:
            found.setdefault(match.group(1), []).append(match.group(2))
    return found


def parse_links(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in text.splitlines():
        match = _MAC.search(line.strip())
        if match:
            found[match.group(1).rstrip(":")] = match.group(2)
    return found


def parse_gateway(text: str) -> str:
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "default" and parts[1] == "via":
            return parts[2]
    return ""


def parse_dns(text: str) -> list[str]:
    servers: list[str] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "nameserver":
            servers.append(parts[1])
    return servers


def parse_routes(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()][:20]


def parse_ports(text: str) -> list[int]:
    ports: set[int] = set()
    for line in text.splitlines():
        if "LISTEN" not in line.upper():
            continue
        match = _PORT.search(line)
        if match:
            ports.add(int(match.group(1)))
    return sorted(ports)


def build_interfaces(addresses: dict[str, list[str]], macs: dict[str, str]) -> list[dict[str, object]]:
    names = sorted(set(addresses) | set(macs))
    return [
        {"name": name, "addresses": addresses.get(name, []), "mac": macs.get(name, "")}
        for name in names
    ]
