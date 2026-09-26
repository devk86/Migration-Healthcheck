import json
from typing import Any


def parse_memory(text: str) -> dict[str, int | float | None]:
    payload = _object(text)
    total_kb = _int(payload.get("TotalVisibleMemorySize"))
    free_kb = _int(payload.get("FreePhysicalMemory"))
    if total_kb is None or free_kb is None:
        return {"total": None, "free": None, "used": None, "used_percent": None}
    total = total_kb * 1024
    free = free_kb * 1024
    used = total - free
    return {
        "total": total,
        "free": free,
        "used": used,
        "used_percent": (used / total * 100) if total else None,
    }


def _object(text: str) -> dict[str, Any]:
    if not text.strip():
        return {}
    loaded = json.loads(text)
    if isinstance(loaded, dict):
        return loaded
    return {}


def _int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return int(value)
    return None
