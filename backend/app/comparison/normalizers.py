from typing import Any


def as_dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def as_list(value: object) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def text(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def os_label(snapshot: dict[str, Any]) -> str:
    os_info = as_dict(snapshot.get("os"))
    distribution = text(os_info.get("distribution") or os_info.get("caption"))
    version = text(os_info.get("distribution_version") or os_info.get("version"))
    return " ".join(part for part in (distribution, version) if part)


def hostname(snapshot: dict[str, Any]) -> str:
    return text(as_dict(snapshot.get("os")).get("hostname") or as_dict(snapshot.get("os")).get("computer_name"))


def addresses(snapshot: dict[str, Any]) -> list[str]:
    network = as_dict(snapshot.get("network"))
    found: list[str] = []
    for item in as_list(network.get("interfaces")):
        if not isinstance(item, dict):
            continue
        for address in as_list(item.get("addresses")):
            if isinstance(address, str) and address:
                found.append(address)
    return sorted(set(found))


def services(snapshot: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in as_list(as_dict(snapshot.get("services")).get("items")):
        if not isinstance(item, dict):
            continue
        name = text(item.get("name"))
        if name:
            result[name] = text(item.get("status")).lower() or "unknown"
    return result


def volumes(snapshot: dict[str, Any]) -> dict[str, float]:
    result: dict[str, float] = {}
    for item in as_list(as_dict(snapshot.get("disk")).get("volumes")):
        if not isinstance(item, dict):
            continue
        mount = text(item.get("mount") or item.get("drive"))
        usage = number(item.get("usage_percent"))
        if mount and usage is not None:
            result[mount] = usage
    return result
