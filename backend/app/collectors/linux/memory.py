def parse_memory(text: str) -> dict[str, int | float | None]:
    memory: dict[str, int] = {}
    swap: dict[str, int] = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        if parts[0] == "Mem:" and len(parts) >= 7:
            memory = {
                "total": int(parts[1]),
                "used": int(parts[2]),
                "free": int(parts[3]),
                "available": int(parts[6]),
            }
        elif parts[0] == "Swap:" and len(parts) >= 3:
            swap = {"swap_total": int(parts[1]), "swap_used": int(parts[2])}
    total = memory.get("total")
    used = memory.get("used")
    used_percent = (used / total * 100) if total and used is not None else None
    return {
        "total": memory.get("total"),
        "available": memory.get("available"),
        "used": used,
        "free": memory.get("free"),
        "swap_total": swap.get("swap_total"),
        "swap_used": swap.get("swap_used"),
        "used_percent": used_percent,
    }
