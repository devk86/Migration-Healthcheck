import re

_SERVICE = re.compile(r"\[\s*([+\-?])\s*\]\s+(\S+)")


def parse_systemctl_units(text: str) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for line in text.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 4 or not parts[0].endswith(".service"):
            continue
        name = parts[0].removesuffix(".service")
        sub = parts[3]
        items.append(
            {
                "name": name,
                "status": "running" if sub == "running" else "stopped",
                "enabled": None,
                "description": parts[4] if len(parts) > 4 else "",
            }
        )
    return items


def parse_enabled(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].endswith(".service"):
            found[parts[0].removesuffix(".service")] = parts[1]
    return found


def parse_service_status_all(text: str) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for line in text.splitlines():
        match = _SERVICE.search(line)
        if not match:
            continue
        flag, name = match.group(1), match.group(2)
        items.append(
            {
                "name": name,
                "status": "running" if flag == "+" else "stopped",
                "enabled": None,
                "description": "",
            }
        )
    return items


def merge_enabled(items: list[dict[str, object]], enabled: dict[str, str]) -> list[dict[str, object]]:
    known = {str(item.get("name", "")) for item in items}
    for item in items:
        name = str(item.get("name", ""))
        if name in enabled:
            item["enabled"] = enabled[name] == "enabled"
    for name, state in enabled.items():
        if name in known:
            continue
        items.append(
            {
                "name": name,
                "status": "stopped",
                "enabled": state == "enabled",
                "description": "",
            }
        )
    return items
