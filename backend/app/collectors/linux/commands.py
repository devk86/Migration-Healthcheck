HOSTNAME = "hostname"
OS_RELEASE = "cat /etc/os-release"
KERNEL = "uname -r"
ARCH = "uname -m"
UPTIME = "cat /proc/uptime"
TIMEZONE = "timedatectl show -p Timezone --value"
TIMEZONE_FALLBACK = "cat /etc/timezone"
CPUINFO = "cat /proc/cpuinfo"
LOADAVG = "cat /proc/loadavg"
CPU_USAGE = "awk '/^cpu /{print ($2+$4)*100/($2+$4+$5)}' /proc/stat"
MEMORY = "free -b"
DISK = "df -PT"
NET_ADDR = "ip -4 -o addr"
NET_LINK = "ip -o link"
NET_ROUTE = "ip route"
NET_DNS = "cat /etc/resolv.conf"
NET_LISTEN = "ss -lntu"
SERVICES = "systemctl list-units --type=service --all --no-legend --no-pager --plain"
SERVICES_FALLBACK = "service --status-all"
SERVICE_ENABLED = "systemctl list-unit-files --type=service --no-legend --no-pager"
PROCESSES = "ps -eo pid,user,pcpu,pmem,comm --no-headers --sort=-pmem"
PACKAGES = (
    'sh -c "if command -v dpkg-query >/dev/null 2>&1; then echo MANAGER=apt; '
    "dpkg-query -W -f '\\${Package}\\t\\${Version}\\n'; "
    'elif command -v rpm >/dev/null 2>&1; then echo MANAGER=rpm; '
    "rpm -qa --queryformat '%{NAME}\\t%{VERSION}-%{RELEASE}\\n'; "
    'else echo MANAGER=unknown; fi"'
)

ALLOWED = {
    HOSTNAME,
    OS_RELEASE,
    KERNEL,
    ARCH,
    UPTIME,
    TIMEZONE,
    TIMEZONE_FALLBACK,
    CPUINFO,
    LOADAVG,
    CPU_USAGE,
    MEMORY,
    DISK,
    NET_ADDR,
    NET_LINK,
    NET_ROUTE,
    NET_DNS,
    NET_LISTEN,
    SERVICES,
    SERVICES_FALLBACK,
    SERVICE_ENABLED,
    PROCESSES,
    PACKAGES,
}
