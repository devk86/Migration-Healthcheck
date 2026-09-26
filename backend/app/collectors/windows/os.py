import json
from typing import Any


def parse_os(text: str) -> dict[str, str]:
    payload = _object(text)
    return {
        "computer_name": _text(payload.get("CSName")),
        "hostname": _text(payload.get("CSName")),
        "caption": _text(payload.get("Caption")),
        "distribution": _text(payload.get("Caption")),
        "version": _text(payload.get("Version")),
        "distribution_version": _text(payload.get("Version")),
        "build_number": _text(payload.get("BuildNumber")),
        "architecture": _text(payload.get("OSArchitecture")),
        "last_boot": _text(payload.get("LastBootUpTime")),
    }


def parse_timezone(text: str) -> str:
    return text.strip()


def _object(text: str) -> dict[str, Any]:
    if not text.strip():
        return {}
    loaded = json.loads(text)
    if isinstance(loaded, list):
        first = loaded[0] if loaded else {}
        return first if isinstance(first, dict) else {}
    if isinstance(loaded, dict):
        return loaded
    return {}


def _text(value: object) -> str:
    if value is None:
        return ""
    return str(value)
