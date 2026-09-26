PSEUDO = {
    "tmpfs",
    "devtmpfs",
    "overlay",
    "squashfs",
    "proc",
    "sysfs",
    "cgroup",
    "cgroup2",
    "devpts",
    "mqueue",
    "bpf",
    "tracefs",
    "securityfs",
    "pstore",
    "autofs",
    "configfs",
    "debugfs",
    "hugetlbfs",
    "ramfs",
    "efivarfs",
}


def parse_disk(text: str) -> dict[str, list[dict[str, object]]]:
    volumes: list[dict[str, object]] = []
    for line in text.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 7:
            continue
        filesystem_type = parts[1]
        if filesystem_type in PSEUDO:
            continue
        try:
            total = int(parts[2]) * 1024
            used = int(parts[3]) * 1024
            available = int(parts[4]) * 1024
            usage = float(parts[5].rstrip("%"))
        except ValueError:
            continue
        volumes.append(
            {
                "device": parts[0],
                "filesystem": filesystem_type,
                "total": total,
                "used": used,
                "available": available,
                "usage_percent": usage,
                "mount": parts[-1],
            }
        )
    return {"volumes": volumes}
