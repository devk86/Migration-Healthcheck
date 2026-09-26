import csv
import io
import json
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.errors import NotFoundError, ValidationFailed
from app.models import Comparison, Report, Server, Snapshot
from app.services.audit import record
from app.services.comparison_service import list_results
from app.storage.local import snapshot_storage
from app.utils.filesystem import safe_path

FORMATS = {"json", "csv", "html", "xlsx", "pdf"}
HTML_DOCUMENTS = {"pre", "post", "comparison"}
SNAPSHOT_SECTIONS = ("os", "cpu", "memory", "disk", "network", "services", "processes", "software")


async def create_report(
    session: Session,
    *,
    comparison_id: uuid.UUID,
    report_format: str,
    actor: str,
    user_id: uuid.UUID | None,
) -> Report:
    if report_format not in FORMATS:
        raise ValidationFailed("Report format is not supported.")
    comparison = session.get(Comparison, comparison_id)
    if comparison is None:
        raise NotFoundError("Comparison was not found.")
    server = session.get(Server, comparison.server_id)
    pre = session.get(Snapshot, comparison.pre_snapshot_id)
    post = session.get(Snapshot, comparison.post_snapshot_id)
    if server is None or pre is None or post is None:
        raise NotFoundError("Comparison data is incomplete.")
    pre_body = await snapshot_storage().load(pre.path)
    post_body = await snapshot_storage().load(post.path)
    rows = list_results(session, comparison.id)
    payload = _payload(server, comparison, pre, post, pre_body, post_body, rows)
    report = Report(
        comparison_id=comparison.id,
        format=report_format,
        path="",
        created_by=user_id,
    )
    session.add(report)
    session.flush()
    path = _write(report.id, report_format, payload)
    report.path = str(path)
    record(session, actor, "report.create", f"{report_format}:{report.id}")
    session.commit()
    session.refresh(report)
    return report


def list_reports(session: Session) -> list[Report]:
    return list(session.scalars(select(Report).order_by(Report.created_at.desc())))


def list_report_choices(session: Session) -> list[dict[str, Any]]:
    servers = list(session.scalars(select(Server).order_by(Server.name)))
    latest: dict[tuple[uuid.UUID, str], Snapshot] = {}
    for snapshot in session.scalars(select(Snapshot).order_by(Snapshot.created_at.desc())):
        latest.setdefault((snapshot.server_id, snapshot.phase), snapshot)
    latest_comparison: dict[uuid.UUID, Comparison] = {}
    for comparison in session.scalars(select(Comparison).order_by(Comparison.created_at.desc())):
        latest_comparison.setdefault(comparison.server_id, comparison)
    choices: list[dict[str, Any]] = []
    for server in servers:
        pre = latest.get((server.id, "PRE"))
        post = latest.get((server.id, "POST"))
        if pre is not None:
            choices.append(_choice(server, "pre", pre.id, None))
        if post is not None:
            choices.append(_choice(server, "post", post.id, None))
        comparison = latest_comparison.get(server.id)
        if pre is not None and post is not None:
            choices.append(_choice(server, "comparison", None, comparison.id if comparison else None))
    return choices


def _choice(
    server: Server,
    kind: str,
    snapshot_id: uuid.UUID | None,
    comparison_id: uuid.UUID | None,
) -> dict[str, Any]:
    return {
        "server_id": server.id,
        "server_name": server.name,
        "kind": kind,
        "snapshot_id": snapshot_id,
        "comparison_id": comparison_id,
    }


async def html_document(session: Session, comparison_id: uuid.UUID, document: str) -> tuple[str, str]:
    if document not in HTML_DOCUMENTS:
        raise ValidationFailed("HTML document must be pre, post, or comparison.")
    comparison = session.get(Comparison, comparison_id)
    if comparison is None:
        raise NotFoundError("Comparison was not found.")
    server = session.get(Server, comparison.server_id)
    pre = session.get(Snapshot, comparison.pre_snapshot_id)
    post = session.get(Snapshot, comparison.post_snapshot_id)
    if server is None or pre is None or post is None:
        raise NotFoundError("Comparison data is incomplete.")
    filename = _download_name(server.name, document)
    if document == "comparison":
        pre_body = await snapshot_storage().load(pre.path)
        post_body = await snapshot_storage().load(post.path)
        payload = _payload(server, comparison, pre, post, pre_body, post_body, list_results(session, comparison.id))
        return filename, _html(payload)
    snapshot = pre if document == "pre" else post
    body = await snapshot_storage().load(snapshot.path)
    collected = ""
    collection = body.get("collection")
    if isinstance(collection, dict):
        collected = str(collection.get("collected_at") or "")
    return filename, _snapshot_html(server.name, document.upper(), collected, body)


async def snapshot_html_document(session: Session, snapshot_id: uuid.UUID) -> tuple[str, str]:
    snapshot = session.get(Snapshot, snapshot_id)
    if snapshot is None:
        raise NotFoundError("Snapshot was not found.")
    server = session.get(Server, snapshot.server_id)
    if server is None:
        raise NotFoundError("Server was not found.")
    body = await snapshot_storage().load(snapshot.path)
    collected = ""
    collection = body.get("collection")
    if isinstance(collection, dict):
        collected = str(collection.get("collected_at") or "")
    phase = snapshot.phase.lower()
    return _download_name(server.name, phase), _snapshot_html(server.name, snapshot.phase, collected, body)


def report_file(report: Report) -> Path:
    root = Path(get_settings().data_dir) / "reports"
    candidate = Path(report.path).resolve()
    if not candidate.is_relative_to(root.resolve()) or not candidate.is_file():
        raise NotFoundError("Report file was not found.")
    return candidate


def _payload(
    server: Server,
    comparison: Comparison,
    pre: Snapshot,
    post: Snapshot,
    pre_body: dict[str, Any],
    post_body: dict[str, Any],
    rows: list[Any],
) -> dict[str, Any]:
    os_info = post_body.get("os") if isinstance(post_body.get("os"), dict) else {}
    os_name = ""
    if isinstance(os_info, dict):
        os_name = " ".join(
            part
            for part in (
                str(os_info.get("distribution") or os_info.get("caption") or ""),
                str(os_info.get("distribution_version") or os_info.get("version") or ""),
            )
            if part
        )
    return {
        "server": server.name,
        "address": server.address,
        "os": os_name,
        "pre_timestamp": pre.created_at.isoformat(),
        "post_timestamp": post.created_at.isoformat(),
        "overall_status": comparison.overall_status,
        "rows": [
            {
                "category": row.category,
                "metric": row.metric,
                "pre": row.pre_value,
                "post": row.post_value,
                "change": row.change,
                "status": row.status,
            }
            for row in rows
        ],
        "warnings": [row.metric for row in rows if row.status == "WARN"],
        "failures": [row.metric for row in rows if row.status == "FAIL"],
    }


def _write(report_id: uuid.UUID, report_format: str, payload: dict[str, Any]) -> Path:
    root = Path(get_settings().data_dir) / "reports"
    root.mkdir(parents=True, exist_ok=True)
    path = safe_path(root, f"{report_id}.{report_format}")
    if report_format == "json":
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    elif report_format == "csv":
        path.write_text(_csv(payload), encoding="utf-8")
    elif report_format == "html":
        path.write_text(_html(payload), encoding="utf-8")
    elif report_format == "xlsx":
        _xlsx(path, payload)
    else:
        _pdf(path, payload)
    return path


def _csv(payload: dict[str, Any]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["server", payload["server"]])
    writer.writerow(["os", payload["os"]])
    writer.writerow(["pre_timestamp", payload["pre_timestamp"]])
    writer.writerow(["post_timestamp", payload["post_timestamp"]])
    writer.writerow(["overall_status", payload["overall_status"]])
    writer.writerow([])
    writer.writerow(["category", "metric", "pre", "post", "change", "status"])
    for row in payload["rows"]:
        if isinstance(row, dict):
            writer.writerow([row["category"], row["metric"], row["pre"], row["post"], row["change"], row["status"]])
    return buffer.getvalue()


def _html(payload: dict[str, Any]) -> str:
    body = "".join(
        "<tr>"
        + "".join(
            f"<td>{_escape(str(row[key]))}</td>"
            for key in ("category", "metric", "pre", "post", "change", "status")
        )
        + "</tr>"
        for row in payload["rows"]
        if isinstance(row, dict)
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>Migration report</title></head><body>"
        f"<h1>{_escape(str(payload['server']))}</h1>"
        f"<p>{_escape(str(payload['os']))}</p>"
        f"<p>PRE {_escape(str(payload['pre_timestamp']))}</p>"
        f"<p>POST {_escape(str(payload['post_timestamp']))}</p>"
        f"<p>Overall {_escape(str(payload['overall_status']))}</p>"
        f"<p>Warnings {_escape(', '.join(payload['warnings']))}</p>"
        f"<p>Failures {_escape(', '.join(payload['failures']))}</p>"
        "<table><thead><tr><th>Category</th><th>Metric</th><th>PRE</th><th>POST</th><th>Change</th><th>Status</th></tr></thead>"
        f"<tbody>{body}</tbody></table></body></html>"
    )


def _xlsx(path: Path, payload: dict[str, Any]) -> None:
    from openpyxl import Workbook

    book = Workbook()
    sheet = book.active
    sheet.title = "Comparison"
    sheet.append(["server", payload["server"]])
    sheet.append(["os", payload["os"]])
    sheet.append(["pre_timestamp", payload["pre_timestamp"]])
    sheet.append(["post_timestamp", payload["post_timestamp"]])
    sheet.append(["overall_status", payload["overall_status"]])
    sheet.append([])
    sheet.append(["category", "metric", "pre", "post", "change", "status"])
    for row in payload["rows"]:
        if isinstance(row, dict):
            sheet.append([row["category"], row["metric"], row["pre"], row["post"], row["change"], row["status"]])
    book.save(path)


def _pdf(path: Path, payload: dict[str, Any]) -> None:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table

    styles = getSampleStyleSheet()
    story = [
        Paragraph(f"Server: {payload['server']}", styles["Heading2"]),
        Paragraph(f"OS: {payload['os']}", styles["Normal"]),
        Paragraph(f"PRE: {payload['pre_timestamp']}", styles["Normal"]),
        Paragraph(f"POST: {payload['post_timestamp']}", styles["Normal"]),
        Paragraph(f"Overall: {payload['overall_status']}", styles["Normal"]),
        Spacer(1, 12),
    ]
    data = [["Category", "Metric", "PRE", "POST", "Change", "Status"]]
    for row in payload["rows"]:
        if isinstance(row, dict):
            data.append([str(row[key]) for key in ("category", "metric", "pre", "post", "change", "status")])
    story.append(Table(data, repeatRows=1))
    SimpleDocTemplate(str(path), pagesize=letter).build(story)


def _snapshot_html(server_name: str, phase: str, collected_at: str, body: dict[str, Any]) -> str:
    sections = []
    for name in SNAPSHOT_SECTIONS:
        value = body.get(name)
        if value is None:
            continue
        sections.append(f"<h2>{_escape(name)}</h2>{_render(value)}")
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{_escape(server_name)} {phase}</title>"
        "<style>body{font-family:sans-serif;margin:2rem}table{border-collapse:collapse;margin:0 0 1.5rem}"
        "th,td{border:1px solid #d3dde3;padding:0.35rem 0.5rem;text-align:left;vertical-align:top}</style></head><body>"
        f"<h1>{_escape(server_name)}</h1>"
        f"<p>{_escape(phase)} {_escape(collected_at)}</p>"
        f"{''.join(sections)}</body></html>"
    )


def _render(value: Any) -> str:
    if isinstance(value, dict):
        rows = "".join(
            f"<tr><th>{_escape(str(key))}</th><td>{_render(item)}</td></tr>" for key, item in value.items()
        )
        return f"<table>{rows}</table>"
    if isinstance(value, list):
        if value and all(isinstance(item, dict) for item in value):
            keys: list[str] = []
            for item in value:
                for key in item:
                    if key not in keys:
                        keys.append(str(key))
            head = "".join(f"<th>{_escape(key)}</th>" for key in keys)
            body = "".join(
                "<tr>" + "".join(f"<td>{_render(item.get(key, ''))}</td>" for key in keys) + "</tr>" for item in value
            )
            return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
        return "<ul>" + "".join(f"<li>{_escape(str(item))}</li>" for item in value) + "</ul>"
    return _escape(str(value))


def _download_name(server_name: str, document: str) -> str:
    stem = "".join(char if char.isalnum() or char in "-_." else "-" for char in server_name).strip("-") or "server"
    return f"{stem}-{document}.html"


def _escape(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
