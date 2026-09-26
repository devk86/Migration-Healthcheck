import json

from app.collectors.linux import commands as linux
from app.collectors.windows import commands as windows

_LINUX_BASE = {
    linux.HOSTNAME: "web01\n",
    linux.OS_RELEASE: 'NAME="Ubuntu"\nVERSION_ID="24.04"\nID=ubuntu\n',
    linux.KERNEL: "6.8.0-40-generic\n",
    linux.ARCH: "x86_64\n",
    linux.UPTIME: "270720.00 1000.00\n",
    linux.TIMEZONE: "UTC\n",
    linux.CPUINFO: (
        "processor\t: 0\nmodel name\t: Intel Xeon\ncpu cores\t: 4\nsiblings\t: 8\nphysical id\t: 0\n"
        "processor\t: 1\nmodel name\t: Intel Xeon\ncpu cores\t: 4\nsiblings\t: 8\nphysical id\t: 0\n"
    ),
    linux.LOADAVG: "0.10 0.20 0.30 1/100 10\n",
    linux.CPU_USAGE: "12.5\n",
    linux.MEMORY: (
        "              total        used        free      shared  buff/cache   available\n"
        "Mem:     34359738368  8589934592  8589934592     0     17179869184  25769803776\n"
        "Swap:     2147483648           0  2147483648\n"
    ),
    linux.DISK: (
        "Filesystem     Type  1024-blocks      Used Available Capacity Mounted on\n"
        "/dev/sda1      ext4     104857600  65011712  39845888      62% /\n"
        "tmpfs          tmpfs      1024000         0   1024000       0% /dev/shm\n"
    ),
    linux.NET_ADDR: "2: eth0    inet 192.168.1.20/24 brd 192.168.1.255 scope global eth0\n",
    linux.NET_LINK: (
        "2: eth0: <BROADCAST> mtu 1500 qdisc fq state UP mode DEFAULT "
        "link/ether aa:bb:cc:dd:ee:01 brd ff:ff:ff:ff:ff:ff\n"
    ),
    linux.NET_ROUTE: "default via 192.168.1.1 dev eth0\n",
    linux.NET_DNS: "nameserver 1.1.1.1\n",
    linux.NET_LISTEN: "tcp LISTEN 0 128 0.0.0.0:22 0.0.0.0:*\ntcp LISTEN 0 128 0.0.0.0:80 0.0.0.0:*\n",
    linux.SERVICES: (
        "nginx.service loaded active running Nginx\n"
        "postgres.service loaded active running PostgreSQL\n"
    ),
    linux.SERVICE_ENABLED: "nginx.service enabled\npostgres.service enabled\n",
    linux.PROCESSES: (
        "1 root 0.1 0.2 systemd\n"
        "42 www-data 1.0 2.5 nginx\n"
        "88 postgres 0.4 1.8 postgres\n"
        "120 root 0.0 0.3 sshd\n"
    ),
    linux.PACKAGES: (
        "MANAGER=apt\n"
        "nginx\t1.24.0\n"
        "postgresql-common\t257\n"
        "openssh-server\t1:9.6p1-3\n"
        "python3\t3.12.3-0ubuntu1\n"
    ),
}


def stdout_for(os_type: str, name: str, phase: str, command: str) -> tuple[str, int]:
    if os_type == "linux":
        return _linux(name, phase, command), 0
    if os_type == "windows":
        return _windows(name, phase, command), 0
    return "", 1


def _linux(name: str, phase: str, command: str) -> str:
    text = _LINUX_BASE.get(command, "")
    host = name.removeprefix("linux-")
    if command == linux.HOSTNAME:
        text = f"{host}\n"
    if name == "linux-web01" and phase == "POST" and command == linux.DISK:
        text = text.replace("62%", "68%")
    if name == "linux-web01" and phase == "POST" and command == linux.NET_ADDR:
        text = text.replace("192.168.1.20", "10.0.0.20")
    if name == "linux-db01" and phase == "POST" and command == linux.SERVICES:
        text = text.replace("postgres.service loaded active running", "postgres.service loaded inactive dead")
    return text


def _windows(name: str, phase: str, command: str) -> str:
    computer = name.removeprefix("windows-").upper()
    if command == windows.OS:
        if name == "windows-db01" and phase == "POST":
            computer = "WIN-DB01-NEW"
        return json.dumps(
            {
                "CSName": computer,
                "Caption": "Microsoft Windows Server 2022",
                "Version": "10.0.20348",
                "BuildNumber": "20348",
                "OSArchitecture": "64-bit",
                "LastBootUpTime": "2026-01-01T00:00:00Z",
            }
        )
    if command == windows.TIMEZONE:
        return "UTC\n"
    if command == windows.CPU:
        return json.dumps(
            {
                "Name": "Intel Xeon",
                "Manufacturer": "GenuineIntel",
                "NumberOfCores": 4,
                "NumberOfLogicalProcessors": 8,
                "MaxClockSpeed": 2400,
                "LoadPercentage": 15,
            }
        )
    if command == windows.MEMORY:
        total = 33554432
        if name == "windows-app01" and phase == "POST":
            total = 41943040
        return json.dumps({"TotalVisibleMemorySize": total, "FreePhysicalMemory": 8388608})
    if command == windows.DISK:
        return json.dumps(
            {"DeviceID": "C:", "FileSystem": "NTFS", "Size": 107374182400, "FreeSpace": 64424509440}
        )
    if command == windows.NETWORK:
        return json.dumps(
            {
                "adapters": [
                    {
                        "Description": "Ethernet",
                        "MACAddress": "00:11:22:33:44:55",
                        "IPAddress": ["192.168.1.30"],
                        "DefaultIPGateway": ["192.168.1.1"],
                        "DNSServerSearchOrder": ["1.1.1.1"],
                    }
                ],
                "routes": [{"DestinationPrefix": "0.0.0.0/0", "NextHop": "192.168.1.1"}],
                "ports": [80, 443],
            }
        )
    if command == windows.SERVICES:
        return json.dumps(
            [
                {
                    "Name": "W3SVC",
                    "DisplayName": "World Wide Web Publishing",
                    "State": "Running",
                    "StartMode": "Auto",
                    "StartName": "LocalSystem",
                }
            ]
        )
    if command == windows.PROCESSES:
        return json.dumps([{"Name": "w3wp", "Id": 1200, "CPU": 1.2, "WorkingSet": 104857600}])
    if command == windows.SOFTWARE:
        return json.dumps([{"DisplayName": "IIS", "DisplayVersion": "10.0"}])
    return ""
