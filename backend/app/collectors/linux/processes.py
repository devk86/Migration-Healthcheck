def parse_processes(text: str) -> dict[str, list[dict[str, object]]]:
    items: list[dict[str, object]] = []
    for line in text.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        try:
            pid = int(parts[0])
            cpu = float(parts[2])
            memory = float(parts[3])
        except ValueError:
            continue
        items.append(
            {
                "pid": pid,
                "user": parts[1],
                "cpu": cpu,
                "memory": memory,
                "name": parts[4],
                "command": parts[4],
            }
        )
    return {"items": items}
