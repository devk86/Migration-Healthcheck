import io
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ValidationFailed
from app.models import Server
from app.services.audit import record

SECRET_HEADERS = {"password", "secret", "private key", "private_key", "credential"}


def parse_csv(content: bytes) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if b"\x00" in content:
        raise ValidationFailed("CSV file is not valid text.")
    try:
        frame = pd.read_csv(io.BytesIO(content), dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except Exception as exc:
        raise ValidationFailed("CSV file could not be read.") from exc
    columns = [str(column).strip() for column in frame.columns]
    frame.columns = columns
    lowered = {column.lower() for column in columns}
    if SECRET_HEADERS & lowered:
        raise ValidationFailed("CSV must not contain credentials.")
    lookup = {column.casefold(): column for column in columns}
    name_column = lookup.get("server name/ip")
    os_column = lookup.get("os name")
    if name_column is None or os_column is None:
        raise ValidationFailed("CSV is missing required columns.")
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, record_row in enumerate(frame.to_dict(orient="records")):
        line = index + 2
        name = str(record_row.get(name_column, "")).strip()
        os_name = str(record_row.get(os_column, "")).strip().lower()
        if not name and not os_name:
            continue
        if not name:
            errors.append({"line": line, "message": "Server name is empty."})
            continue
        if not os_name:
            errors.append({"line": line, "message": "OS name is empty."})
            continue
        if os_name not in {"linux", "windows"}:
            errors.append({"line": line, "message": f"OS '{os_name}' is not supported."})
            continue
        key = name.lower()
        if key in seen:
            errors.append({"line": line, "message": "Duplicate server in the file."})
            continue
        seen.add(key)
        rows.append({"line": line, "name": name, "os_type": os_name})
    return rows, errors


def import_servers(
    session: Session,
    content: bytes,
    *,
    mode: str,
    actor: str,
) -> dict[str, Any]:
    if mode not in {"preview", "import"}:
        raise ValidationFailed("Mode must be preview or import.")
    rows, errors = parse_csv(content)
    existing_names = {name.lower() for name in session.scalars(select(Server.name))}
    for row in rows:
        if row["name"].lower() in existing_names:
            errors.append({"line": row["line"], "message": "Server already exists."})
    if mode == "preview" or errors:
        return {"mode": mode, "imported": 0, "rows": rows, "errors": errors}
    for row in rows:
        session.add(
            Server(name=row["name"], address=row["name"], os_type=row["os_type"], enabled=True)
        )
    record(session, actor, "servers.import", f"{len(rows)} servers")
    session.commit()
    return {"mode": mode, "imported": len(rows), "rows": rows, "errors": []}
