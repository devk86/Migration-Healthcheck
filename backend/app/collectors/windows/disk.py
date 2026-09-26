import json
from typing import Any


def parse_disk(text: str) -> dict[str, list[dict[str, object]]]:
    volumes: list[dict[str, object]] = []
    for row in _rows(text):
        size = _int(row.get("Size"))
        free = _int(row.get("FreeSpace"))
        if size is None or free is None or size == 0:
            continue
        used = size - free
        volumes.append(
            {
                "drive": _text(row.get("DeviceID")),
                "mount": _text(row.get("DeviceID")),
                "filesystem": _text(row.get("FileSystem")),
                "total": size,
                "available": free,
                "used": used,
                "usage_percent": used / size * 100,
            }
        )
    return {"volumes": volumes}


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
    return None


def _text(value: object) -> str:
    return "" if value is None else str(value)
