# Collectors

Linux and Windows collectors share the same normalized snapshot shape: `schema_version`, `server`, `collection`, `os`, `cpu`, `memory`, `disk`, `network`, `services`, `processes`, and `software`.

Linux commands are fixed strings in `app/collectors/linux/commands.py` (`hostname`, `/etc/os-release`, `uname`, `free -b`, `df -PT`, `ip`, `ss`, `systemctl`, with a `service --status-all` fallback). Pseudo filesystems such as `tmpfs` are skipped. Package output is a manager, a count, and tab-separated important packages.

Windows collection uses CIM and PowerShell, one command per category, parsed from JSON. Service account names are collected. Passwords are not.

The connector rejects any command that is not in the allowlist. The API does not accept a command from the browser.

With `MOCK_CONNECTORS=true`, both operating systems return deterministic output. `linux-web01` changes disk usage and IP after migration. `linux-db01` stops postgres. `windows-app01` grows memory. `windows-db01` changes hostname.
