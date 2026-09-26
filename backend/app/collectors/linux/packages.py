def parse_packages(text: str) -> dict[str, object]:
    manager = "unknown"
    count = 0
    packages: list[dict[str, str]] = []
    for line in text.splitlines():
        if line.startswith("MANAGER="):
            manager = line.split("=", 1)[1].strip()
        elif line.startswith("COUNT="):
            try:
                count = int(line.split("=", 1)[1].strip())
            except ValueError:
                count = 0
        elif "\t" in line:
            name, version = line.split("\t", 1)
            if name.strip():
                packages.append({"name": name.strip(), "version": version.strip()})
    if count == 0:
        count = len(packages)
    return {"manager": manager, "count": count, "packages": packages}
