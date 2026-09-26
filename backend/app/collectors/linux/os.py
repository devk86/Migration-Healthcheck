def parse_os_release(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"')
    return {
        "distribution": data.get("NAME") or data.get("ID") or "",
        "distribution_version": data.get("VERSION_ID") or "",
    }


def parse_uptime(text: str) -> int | None:
    token = text.strip().split()
    if not token:
        return None
    try:
        return int(float(token[0]))
    except ValueError:
        return None


def parse_timezone(text: str) -> str:
    value = text.strip()
    if value.lower().startswith("timezone="):
        return value.split("=", 1)[1].strip()
    return value.splitlines()[0].strip() if value else ""
