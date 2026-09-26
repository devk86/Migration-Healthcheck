import json
from typing import Any


def parse_cpu(text: str) -> dict[str, object]:
    rows = _rows(text)
    if not rows:
        return {}
    cores = sum(_int(row.get("NumberOfCores")) or 0 for row in rows)
    threads = sum(_int(row.get("NumberOfLogicalProcessors")) or 0 for row in rows)
    loads = [_int(row.get("LoadPercentage")) for row in rows]
    sampled = [value for value in loads if value is not None]
    return {
        "name": _text(rows[0].get("Name")),
        "manufacturer": _text(rows[0].get("Manufacturer")),
        "cores": cores or None,
        "logical_processors": threads or None,
        "max_clock_speed": _int(rows[0].get("MaxClockSpeed")),
        "usage_percent": (sum(sampled) / len(sampled)) if sampled else None,
    }


def _rows(text: str) -> list[dict[str, Any]]:
    if not text.strip():
        return []
    loaded = json.loads(text)
    if isinstance(loaded, dict):
        return [loaded]
    if isinstance(loaded, list):
        return [item for item in loaded if isinstance(item, dict)]
    return []


def _int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _text(value: object) -> str:
    return "" if value is None else str(value)
