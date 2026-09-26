from pathlib import Path

from app.errors import StorageFailed


def safe_path(root: Path, *parts: str) -> Path:
    if any(part in {"", ".", ".."} or "/" in part or "\\" in part for part in parts):
        raise StorageFailed("Path is not allowed.")
    base = root.resolve()
    candidate = base.joinpath(*parts).resolve()
    if not candidate.is_relative_to(base):
        raise StorageFailed("Path is not allowed.")
    return candidate
