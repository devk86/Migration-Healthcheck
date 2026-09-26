from typing import Any

from app.comparison.normalizers import (
    addresses,
    as_dict,
    hostname,
    number,
    os_label,
    services,
    volumes,
)
from app.comparison.rows import ComparisonRow


def _row(
    category: str,
    metric: str,
    pre_value: str,
    post_value: str,
    change: str,
    status: str,
) -> ComparisonRow:
    return ComparisonRow(
        category=category,
        metric=metric,
        pre_value=pre_value,
        post_value=post_value,
        change=change,
        status=status,
        changed=pre_value != post_value,
    )


def _missing(category: str, metric: str) -> ComparisonRow:
    return _row(category, metric, "", "", "—", "NOT_CHECKED")


def compare_cpu(pre: dict[str, Any], post: dict[str, Any]) -> list[ComparisonRow]:
    pre_cores = number(as_dict(pre.get("cpu")).get("cores"))
    post_cores = number(as_dict(post.get("cpu")).get("cores"))
    if pre_cores is None or post_cores is None:
        return [_missing("cpu", "cores")]
    status = "PASS" if int(pre_cores) == int(post_cores) else "WARN"
    return [
        _row("cpu", "cores", str(int(pre_cores)), str(int(post_cores)), str(int(post_cores - pre_cores)), status)
    ]


def compare_memory(pre: dict[str, Any], post: dict[str, Any]) -> list[ComparisonRow]:
    pre_total = number(as_dict(pre.get("memory")).get("total"))
    post_total = number(as_dict(post.get("memory")).get("total"))
    if pre_total is None or post_total is None or pre_total == 0:
        return [_missing("memory", "total")]
    delta = abs(post_total - pre_total) / pre_total * 100
    if delta <= 5:
        status = "PASS"
    elif delta <= 20:
        status = "WARN"
    else:
        status = "FAIL"
    return [
        _row(
            "memory",
            "total",
            _gb(pre_total),
            _gb(post_total),
            f"{delta:.1f}%",
            status,
        )
    ]


def compare_disk(pre: dict[str, Any], post: dict[str, Any]) -> list[ComparisonRow]:
    pre_volumes = volumes(pre)
    post_volumes = volumes(post)
    if not pre_volumes and not post_volumes:
        return [_missing("disk", "usage")]
    rows: list[ComparisonRow] = []
    for mount in sorted(set(pre_volumes) | set(post_volumes)):
        if mount not in pre_volumes or mount not in post_volumes:
            rows.append(
                _row(
                    "disk",
                    mount,
                    _pct(pre_volumes.get(mount)),
                    _pct(post_volumes.get(mount)),
                    "missing",
                    "WARN",
                )
            )
            continue
        delta = post_volumes[mount] - pre_volumes[mount]
        abs_delta = abs(delta)
        if abs_delta <= 5:
            status = "PASS"
        elif abs_delta <= 10:
            status = "WARN"
        else:
            status = "FAIL"
        sign = "+" if delta > 0 else ""
        rows.append(
            _row(
                "disk",
                mount,
                _pct(pre_volumes[mount]),
                _pct(post_volumes[mount]),
                f"{sign}{delta:.0f}",
                status,
            )
        )
    return rows


def compare_services(pre: dict[str, Any], post: dict[str, Any]) -> list[ComparisonRow]:
    pre_services = services(pre)
    post_services = services(post)
    if not pre_services and not post_services:
        return [_missing("services", "services")]
    rows: list[ComparisonRow] = []
    for name in sorted(set(pre_services) | set(post_services)):
        before = pre_services.get(name, "absent")
        after = post_services.get(name, "absent")
        status = _service_status(before, after)
        rows.append(_row("services", name, before, after, "—" if before == after else f"{before} → {after}", status))
    return rows


def compare_os(pre: dict[str, Any], post: dict[str, Any]) -> list[ComparisonRow]:
    before = os_label(pre)
    after = os_label(post)
    if not before and not after:
        return [_missing("os", "identity")]
    status = "PASS" if before == after else "WARN"
    return [_row("os", "identity", before, after, "—" if before == after else "changed", status)]


def compare_hostname(pre: dict[str, Any], post: dict[str, Any]) -> list[ComparisonRow]:
    before = hostname(pre)
    after = hostname(post)
    if not before and not after:
        return [_missing("hostname", "hostname")]
    status = "PASS" if before == after else "WARN"
    return [_row("hostname", "hostname", before, after, "—" if before == after else "changed", status)]


def compare_ip(pre: dict[str, Any], post: dict[str, Any]) -> list[ComparisonRow]:
    before = ", ".join(addresses(pre))
    after = ", ".join(addresses(post))
    if not before and not after:
        return [_missing("ip", "addresses")]
    status = "PASS" if before == after else "INFO"
    return [_row("ip", "addresses", before, after, "—" if before == after else "changed", status)]


def _service_status(before: str, after: str) -> str:
    if before == "running" and after == "running":
        return "PASS"
    if before == "running" and after == "stopped":
        return "FAIL"
    if before == "stopped" and after == "running":
        return "INFO"
    if before == after:
        return "PASS"
    if before == "running" and after == "absent":
        return "FAIL"
    if after == "absent" or before == "absent":
        return "INFO"
    return "WARN"


def _gb(value: float) -> str:
    return f"{value / 1024 / 1024 / 1024:.1f} GB"


def _pct(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.0f}%"

