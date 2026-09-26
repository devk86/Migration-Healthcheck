from app.collectors.linux.collector import LinuxCollector
from app.collectors.windows.collector import WindowsCollector
from app.connectors.base import BaseConnector

ALL_CHECKS = ["os", "cpu", "memory", "disk", "network", "services", "processes", "software"]


def get_collector(os_type: str, connector: BaseConnector, checks: list[str]) -> LinuxCollector | WindowsCollector:
    selected = checks or ALL_CHECKS
    if os_type == "windows":
        return WindowsCollector(connector, selected)
    return LinuxCollector(connector, selected)
