import json
from typing import Any


def parse_processes(text: str) -> dict[str, list[dict[str, object]]]:
    items: list[dict[str, object]] = []
    for row in _rows(text):
        items.append(
            {
                "name": _text(row.get("Name")),
                "pid": _int(row.get("Id")) or 0,
                "cpu": _float(row.get("CPU")),
                "memory": _int(row.get("WorkingSet")) or 0,
            }
        )
    return {"items": items}


def _rows(text: str) -> list[dict[str, Any]]:
    if not text.strip():
        return []
    loaded = json.loads(text)
    if isinstance(loaded, dict):
        return [loaded]
    if isinstance(loaded, list):
        return [item for item in loaded if isinstance(item, dict)]
    return []


def _text(value: object) -> str:
    return "" if value is None else str(value)


def _int(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return int(value)
    return None


def _float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    return None
