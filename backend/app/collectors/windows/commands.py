OS = (
    "Get-CimInstance Win32_OperatingSystem | "
    "Select-Object CSName,Caption,Version,BuildNumber,OSArchitecture,LastBootUpTime | "
    "ConvertTo-Json -Compress"
)
TIMEZONE = "Get-TimeZone | Select-Object -ExpandProperty Id"
CPU = (
    "Get-CimInstance Win32_Processor | "
    "Select-Object Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed,LoadPercentage | "
    "ConvertTo-Json -Compress"
)
MEMORY = (
    "Get-CimInstance Win32_OperatingSystem | "
    "Select-Object TotalVisibleMemorySize,FreePhysicalMemory | ConvertTo-Json -Compress"
)
DISK = (
    "Get-CimInstance Win32_LogicalDisk -Filter \"DriveType=3\" | "
    "Select-Object DeviceID,FileSystem,Size,FreeSpace | ConvertTo-Json -Compress"
)
NETWORK = (
    "$adapters = @(Get-CimInstance Win32_NetworkAdapterConfiguration -Filter \"IPEnabled=true\" | "
    "Select-Object Description,MACAddress,IPAddress,DefaultIPGateway,DNSServerSearchOrder); "
    "$routes = @(Get-NetRoute -AddressFamily IPv4 -ErrorAction SilentlyContinue | "
    "Select-Object DestinationPrefix,NextHop); "
    "$ports = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | "
    "Select-Object -ExpandProperty LocalPort -Unique); "
    "[pscustomobject]@{adapters=$adapters; routes=$routes; ports=$ports} | ConvertTo-Json -Compress -Depth 5"
)
SERVICES = (
    "Get-CimInstance Win32_Service | "
    "Select-Object Name,DisplayName,State,StartMode,StartName | ConvertTo-Json -Compress"
)
PROCESSES = "Get-Process | Select-Object Name,Id,CPU,WorkingSet | ConvertTo-Json -Compress"
SOFTWARE = (
    "$paths = @("
    "'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',"
    "'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'"
    "); "
    "Get-ItemProperty $paths -ErrorAction SilentlyContinue | "
    "Where-Object { $_.DisplayName } | "
    "Select-Object DisplayName,DisplayVersion | ConvertTo-Json -Compress"
)

ALLOWED = {OS, TIMEZONE, CPU, MEMORY, DISK, NETWORK, SERVICES, PROCESSES, SOFTWARE}
