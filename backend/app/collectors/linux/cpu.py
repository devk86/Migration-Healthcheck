import re


def parse_cpuinfo(text: str) -> dict[str, object]:
    model = ""
    cores = None
    sockets: set[str] = set()
    threads = len(re.findall(r"^processor\s*:", text, flags=re.MULTILINE))
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = [part.strip() for part in line.split(":", 1)]
        if key == "model name" and not model:
            model = value
        elif key == "cpu cores" and cores is None:
            cores = _int(value)
        elif key == "physical id":
            sockets.add(value)
    if cores is None:
        cores = threads or None
    return {
        "model": model,
        "sockets": len(sockets) or (1 if threads else None),
        "cores": cores,
        "threads": threads or None,
    }


def parse_loadavg(text: str) -> dict[str, float | None]:
    parts = text.split()
    values: list[float | None] = []
    for index in range(3):
        if index >= len(parts):
            values.append(None)
            continue
        try:
            values.append(float(parts[index]))
        except ValueError:
            values.append(None)
    return {"load_1m": values[0], "load_5m": values[1], "load_15m": values[2]}


def parse_usage(text: str) -> float | None:
    token = text.strip().split()
    if not token:
        return None
    try:
        usage = float(token[0])
    except ValueError:
        return None
    return max(0.0, min(usage, 100.0))


def _int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
