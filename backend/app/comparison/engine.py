from typing import Any

from app.comparison.rows import ComparisonRow
from app.comparison.rules import (
    compare_cpu,
    compare_disk,
    compare_hostname,
    compare_ip,
    compare_memory,
    compare_os,
    compare_services,
)


def overall_status(rows: list[ComparisonRow]) -> str:
    present = {row.status for row in rows}
    for status in ("FAIL", "ERROR", "WARN", "PASS", "INFO", "NOT_CHECKED"):
        if status in present:
            return status
    return "NOT_CHECKED"


def compare(
    pre_snapshot: dict[str, Any],
    post_snapshot: dict[str, Any],
    rules: list[str] | None = None,
) -> dict[str, Any]:
    selected = set(rules or ["cpu", "memory", "disk", "services", "os", "hostname", "ip"])
    rows: list[ComparisonRow] = []
    if "cpu" in selected:
        rows.extend(compare_cpu(pre_snapshot, post_snapshot))
    if "memory" in selected:
        rows.extend(compare_memory(pre_snapshot, post_snapshot))
    if "disk" in selected:
        rows.extend(compare_disk(pre_snapshot, post_snapshot))
    if "services" in selected:
        rows.extend(compare_services(pre_snapshot, post_snapshot))
    if "os" in selected:
        rows.extend(compare_os(pre_snapshot, post_snapshot))
    if "hostname" in selected:
        rows.extend(compare_hostname(pre_snapshot, post_snapshot))
    if "ip" in selected:
        rows.extend(compare_ip(pre_snapshot, post_snapshot))
    return {
        "overall_status": overall_status(rows),
        "categories": [
            {
                "category": row.category,
                "metric": row.metric,
                "pre_value": row.pre_value,
                "post_value": row.post_value,
                "change": row.change,
                "status": row.status,
                "changed": row.changed,
            }
            for row in rows
        ],
    }
