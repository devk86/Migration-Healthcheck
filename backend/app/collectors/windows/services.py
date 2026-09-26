import json
from typing import Any


def parse_services(text: str) -> dict[str, list[dict[str, object]]]:
    items: list[dict[str, object]] = []
    for row in _rows(text):
        state = _text(row.get("State")).lower()
        items.append(
            {
                "name": _text(row.get("Name")),
                "display_name": _text(row.get("DisplayName")),
                "status": "running" if state == "running" else "stopped",
                "start_mode": _text(row.get("StartMode")),
                "account": _text(row.get("StartName")),
            }
        )
    return {"items": [item for item in items if item["name"]][:300]}


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
