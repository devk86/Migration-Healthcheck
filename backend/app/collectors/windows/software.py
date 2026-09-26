import json
from typing import Any


def parse_software(text: str) -> dict[str, object]:
    applications: list[dict[str, str]] = []
    for row in _rows(text):
        name = _text(row.get("DisplayName"))
        if not name:
            continue
        applications.append({"name": name, "version": _text(row.get("DisplayVersion"))})
    return {"applications": applications[:50], "count": len(applications)}


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
