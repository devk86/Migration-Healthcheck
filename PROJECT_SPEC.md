# Migration HealthCheck & Comparison Platform

**Document:** `PROJECT_SPEC.md`  
**Version:** 1.0  
**Target:** Local lab first, Azure-ready architecture  
**Primary use case:** Pre- and post-migration health checks for Linux and Windows servers

## 1. Project Objective

Build a web-based platform that allows migration teams to:

1. Upload a CSV containing servers.
2. Automatically determine whether each server is Linux or Windows.
3. Connect to Linux servers using SSH.
4. Connect to Windows servers using WinRM.
5. Execute standardized health checks.
6. Store raw collector output and normalized results locally.
7. Create immutable PRE and POST migration snapshots.
8. Compare PRE vs POST results.
9. Identify PASS, WARN, FAIL, INFO and NOT_CHECKED conditions.
10. Display results through a web dashboard.
11. Generate downloadable reports.
12. Support up to approximately 50 registered servers initially.
13. Run entirely locally using Docker Compose.
14. Keep the architecture suitable for future Azure deployment.

## 2. Important Implementation Principles

### Principle 1 — Never couple collectors to the API

Use:

```text
FastAPI
  ↓
Job
  ↓
HealthCheck Service
  ↓
Connector
  ↓
Collector
```

Do not place SSH/WinRM collection logic directly inside FastAPI routes.

### Principle 2 — Linux and Windows collectors must implement the same interface

```python
class BaseCollector:
    async def collect(self) -> HealthCheckSnapshot:
        ...
```

Implement:

```text
LinuxCollector
WindowsCollector
```

### Principle 3 — Preserve raw and normalized data

```text
Raw Output
  ↓
Normalization
  ↓
Normalized Snapshot
  ↓
Comparison
```

Never discard the original collector output.

### Principle 4 — PRE and POST snapshots are immutable

A completed snapshot must never be modified. A new check creates a new run.

### Principle 5 — Credentials never belong in CSV

CSV contains only:

```csv
Server name/IP,OS name
```

### Principle 6 — Collectors collect; comparison rules compare

Do not hard-code comparison rules inside collectors.

## 3. Technology Stack

### Backend

- Python 3.14+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- Paramiko
- pywinrm
- pandas
- Celery
- Redis
- PostgreSQL

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- React Router
- TanStack Query
- Recharts

### Infrastructure

- Docker
- Docker Compose

### Testing

- pytest
- pytest-asyncio
- httpx
- Vitest
- React Testing Library
- Playwright

## 4. High-Level Architecture

```text
                         Browser
                            │
                            ▼
                  ┌───────────────────┐
                  │ React Frontend    │
                  └─────────┬─────────┘
                            │ REST API
                            ▼
                  ┌───────────────────┐
                  │ FastAPI           │
                  │ Backend           │
                  └─────────┬─────────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
        PostgreSQL        Redis       Local Storage
             │              │              │
             │              ▼              │
             │       ┌─────────────┐       │
             │       │ Celery      │       │
             │       │ Workers     │       │
             │       └──────┬──────┘       │
             │              │              │
             │       ┌──────┴──────┐       │
             │       ▼             ▼       │
             │     SSH           WinRM     │
             │       │             │       │
             │       ▼             ▼       │
             │    Linux         Windows    │
             │                              
             └──────────────────────────────┘
```

## 5. Repository Structure

```text
migration-healthcheck/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── servers.py
│   │   │   ├── imports.py
│   │   │   ├── healthchecks.py
│   │   │   ├── comparisons.py
│   │   │   ├── reports.py
│   │   │   ├── credentials.py
│   │   │   └── logs.py
│   │   ├── collectors/
│   │   │   ├── base.py
│   │   │   ├── registry.py
│   │   │   ├── linux/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── collector.py
│   │   │   │   ├── os.py
│   │   │   │   ├── cpu.py
│   │   │   │   ├── memory.py
│   │   │   │   ├── disk.py
│   │   │   │   ├── network.py
│   │   │   │   ├── services.py
│   │   │   │   ├── processes.py
│   │   │   │   └── packages.py
│   │   │   └── windows/
│   │   │       ├── __init__.py
│   │   │       ├── collector.py
│   │   │       ├── os.py
│   │   │       ├── cpu.py
│   │   │       ├── memory.py
│   │   │       ├── disk.py
│   │   │       ├── network.py
│   │   │       ├── services.py
│   │   │       ├── processes.py
│   │   │       └── software.py
│   │   ├── connectors/
│   │   │   ├── base.py
│   │   │   ├── ssh.py
│   │   │   └── winrm.py
│   │   ├── comparison/
│   │   │   ├── engine.py
│   │   │   ├── rules.py
│   │   │   └── normalizers.py
│   │   ├── workers/
│   │   │   ├── celery_app.py
│   │   │   └── healthcheck_tasks.py
│   │   ├── models/
│   │   │   ├── server.py
│   │   │   ├── credential.py
│   │   │   ├── healthcheck_run.py
│   │   │   ├── snapshot.py
│   │   │   └── comparison.py
│   │   ├── schemas/
│   │   │   ├── server.py
│   │   │   ├── healthcheck.py
│   │   │   ├── comparison.py
│   │   │   └── common.py
│   │   ├── services/
│   │   │   ├── server_service.py
│   │   │   ├── healthcheck_service.py
│   │   │   ├── comparison_service.py
│   │   │   ├── credential_service.py
│   │   │   └── report_service.py
│   │   ├── database/
│   │   │   ├── database.py
│   │   │   └── migrations/
│   │   └── utils/
│   │       ├── logging.py
│   │       ├── filesystem.py
│   │       └── validation.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── types/
│   │   ├── utils/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── tests/
│   ├── package.json
│   └── Dockerfile
│
├── data/
│   ├── logs/
│   ├── snapshots/
│   ├── comparisons/
│   └── reports/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── PROJECT_SPEC.md
└── docs/
    ├── architecture.md
    ├── api.md
    ├── collectors.md
    └── deployment.md
```

## 6. CSV Specification

Required headers:

```csv
Server name/IP,OS name
```

Valid OS values:

```text
linux
windows
```

Matching must be case-insensitive.

Accepted examples:

```text
linux
Linux
LINUX
windows
Windows
WINDOWS
```

Validation requirements:

- Both required columns must exist.
- Empty server names are rejected.
- Empty OS names are rejected.
- Duplicate servers are detected.
- Invalid OS values are reported.
- Whitespace is trimmed.
- Import should not partially create servers unless explicitly configured.
- Show row-level validation errors.

Example:

```csv
Server name/IP,OS name
web01,linux
192.168.1.20,linux
win01,windows
192.168.1.30,windows
```

## 7. Server Model

Fields:

```text
id
name
address
os_type
enabled
created_at
updated_at
last_pre_check
last_post_check
```

Server identity must use the database `id`, not IP address.

This is required because an IP can change after migration.

## 8. Credential Model

Support initially:

```text
SSH_PASSWORD
SSH_PRIVATE_KEY
WINRM_PASSWORD
```

Never return passwords/private keys/secrets from GET APIs.

Credentials must never be written to:

- CSV
- snapshots
- logs
- browser local storage
- API responses

## 9. Connector Interface

Create:

```python
class BaseConnector(ABC):

    @abstractmethod
    async def connect(self) -> None:
        ...

    @abstractmethod
    async def execute(self, command: str) -> CommandResult:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...

    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult:
        ...
```

Implement:

```text
SSHConnector
WinRMConnector
```

## 10. SSH Connector

Use Paramiko.

Requirements:

- configurable connection timeout
- configurable command timeout
- clear errors
- graceful disconnect
- stdout capture
- stderr capture
- exit code capture
- no credential logging

Example result:

```json
{
  "command": "hostname",
  "stdout": "web01",
  "stderr": "",
  "exit_code": 0
}
```

## 11. WinRM Connector

Use pywinrm.

Support:

```text
HTTP
HTTPS
```

Configuration:

```env
WINRM_PORT=5985
WINRM_TRANSPORT=ntlm
WINRM_SERVER_CERT_VALIDATION=ignore
WINRM_TIMEOUT=30
```

PowerShell commands should be used for Windows collection.

## 12. Snapshot Schema

Every snapshot should contain:

```json
{
  "schema_version": "1.0",
  "server": {},
  "collection": {},
  "os": {},
  "cpu": {},
  "memory": {},
  "disk": {},
  "network": {},
  "services": {},
  "processes": {},
  "software": {}
}
```

## 13. Linux Checks

Collect:

### OS

- hostname
- distribution
- distribution_version
- kernel
- architecture
- uptime
- timezone

Use appropriate commands such as:

```bash
hostname
cat /etc/os-release
uname -r
uname -m
uptime
timedatectl
```

Gracefully handle distributions where commands are unavailable.

### CPU

Collect:

- model
- sockets
- cores
- threads
- architecture
- load 1m
- load 5m
- load 15m
- usage percentage

### Memory

Collect:

- total
- available
- used
- free
- swap total
- swap used

### Disk

Collect:

- device
- mount point
- filesystem
- total
- used
- available
- usage percentage

Avoid treating pseudo-filesystems as normal application storage unless configured.

### Network

Collect:

- interfaces
- IP addresses
- MAC addresses
- gateway
- DNS servers
- routes
- listening ports

### Services

Collect:

- service name
- status
- enabled
- description

Use systemd where available and handle non-systemd systems gracefully.

### Processes

Collect:

- PID
- name
- user
- CPU
- memory
- command

Avoid collecting command-line secrets where possible.

### Packages

Detect common package managers:

```text
apt
dnf
yum
rpm
zypper
```

Collect package count and configurable important packages.

## 14. Windows Checks

### OS

Use CIM/PowerShell.

Collect:

- computer name
- caption
- version
- build number
- architecture
- last boot
- timezone

### CPU

Collect:

- name
- manufacturer
- cores
- logical processors
- max clock speed
- sampled utilization

### Memory

Collect:

- total
- free
- used
- used percentage

### Disk

Collect:

- drive
- filesystem
- size
- free space
- used space
- used percentage

### Network

Collect:

- adapters
- IP addresses
- MAC addresses
- gateway
- DNS
- routes
- listening ports

### Services

Collect:

- name
- display name
- state
- start mode
- service account name

Never collect service account passwords.

### Processes

Collect:

- name
- PID
- CPU
- memory

### Software

Collect configurable installed software/application information.

## 15. HealthCheck States

Run states:

```text
QUEUED
RUNNING
COMPLETED
PARTIAL
FAILED
CANCELLED
```

Category statuses:

```text
PASS
WARN
FAIL
INFO
ERROR
NOT_CHECKED
```

## 16. PRE / POST

Each health-check must explicitly specify:

```text
PRE
```

or:

```text
POST
```

Do not infer phase from timestamp.

## 17. API Endpoints

### Health

```http
GET /api/v1/health
```

### Servers

```http
GET    /api/v1/servers
GET    /api/v1/servers/{id}
POST   /api/v1/servers
PATCH  /api/v1/servers/{id}
DELETE /api/v1/servers/{id}
```

### CSV Import

```http
POST /api/v1/imports/servers
```

### Connectivity

```http
POST /api/v1/servers/{id}/test-connection
```

### Health Checks

```http
POST /api/v1/healthchecks
GET  /api/v1/healthchecks
GET  /api/v1/healthchecks/{id}
POST /api/v1/healthchecks/{id}/cancel
```

### Results

```http
GET /api/v1/healthchecks/{id}/results
GET /api/v1/servers/{id}/snapshots
```

### Comparisons

```http
POST /api/v1/comparisons
GET  /api/v1/comparisons
GET  /api/v1/comparisons/{id}
```

### Reports

```http
POST /api/v1/reports
GET  /api/v1/reports
GET  /api/v1/reports/{id}
```

## 18. Database

Core tables:

```text
servers
credentials
healthcheck_runs
healthcheck_results
snapshots
comparisons
comparison_results
reports
check_profiles
audit_logs
```

Relationship:

```text
Server
  │
  ├── HealthCheckRun
  │      ├── HealthCheckResult
  │      └── Snapshot
  │
  └── Comparison
         └── ComparisonResult
```

## 19. Storage

Use:

```text
data/logs/
data/snapshots/
data/comparisons/
data/reports/
```

Snapshot structure:

```text
data/snapshots/
├── pre/
│   └── {server_id}/
│       └── {run_id}.json
└── post/
    └── {server_id}/
        └── {run_id}.json
```

Logs:

```text
data/logs/
├── pre/
│   └── SERVER/
│       └── RUN_ID/
│           ├── collector.log
│           ├── connection.log
│           └── commands.json
└── post/
    └── SERVER/
        └── RUN_ID/
            ├── collector.log
            ├── connection.log
            └── commands.json
```

Never store secrets in these files.

## 20. Comparison Engine

Implement:

```python
compare(
    pre_snapshot,
    post_snapshot,
    rules
)
```

Output:

```json
{
  "overall_status": "WARN",
  "categories": []
}
```

Default rules:

### CPU

```text
cores unchanged → PASS
cores changed → WARN
```

### Memory

```text
difference <= 5% → PASS
difference > 5% and <= 20% → WARN
difference > 20% → FAIL
```

### Disk

```text
difference <= 5 percentage points → PASS
difference > 5 and <= 10 → WARN
difference > 10 → FAIL
```

### Service

```text
RUNNING → RUNNING = PASS
RUNNING → STOPPED = FAIL
STOPPED → RUNNING = INFO
```

### IP

IP changes should normally be `INFO`, not failure.

### OS

```text
same → PASS
different → WARN
```

### Hostname

```text
same → PASS
different → WARN
```

Rules must be configurable and unit tested.

## 21. Dashboard

Display:

```text
Total Servers
PRE Completed
POST Completed
PASS
WARN
FAIL
Connection Errors
```

Charts:

- server status
- OS distribution
- PRE vs POST status
- failures by category

Filters:

- OS
- phase
- status
- server
- migration wave

## 22. Server Inventory

Columns:

```text
Server
Address
OS
Last PRE
Last POST
Current Status
Connection
Actions
```

Actions:

```text
Test Connection
Run PRE
Run POST
View Details
Compare
View Logs
```

## 23. Server Details

Tabs:

```text
Overview
OS
CPU
Memory
Disk
Network
Services
Processes
Software
PRE
POST
Comparison
Logs
```

## 24. Run Page

Show:

```text
Run ID
Phase
Progress
Completed
Running
Failed
Queued
```

Example:

```text
HealthCheck Run #1001

████████████████░░░░

40 / 50

Completed: 37
Running:    2
Failed:     1
Queued:    10
```

## 25. Comparison UI

Display:

```text
Metric       PRE       POST      Change      Status
----------------------------------------------------
CPU cores    8         8         0          PASS
Memory       32 GB     32 GB     0          PASS
Disk /       62%       67%       +5%        WARN
nginx        Running   Running   —          PASS
postgres     Running   Stopped   —          FAIL
```

Filters:

```text
All
Changes Only
Failures
Warnings
```

## 26. Reports

MVP:

```text
HTML
CSV
JSON
```

Phase 2:

```text
Excel
PDF
```

Report must include:

- server
- OS
- PRE timestamp
- POST timestamp
- overall status
- category results
- changed values
- failures
- warnings

## 27. Check Profiles

Create:

```text
check_profiles
```

Example:

```json
{
  "name": "Default Server",
  "checks": [
    "os",
    "cpu",
    "memory",
    "disk",
    "network",
    "services",
    "processes"
  ]
}
```

Future profiles:

```text
Web Server
Database Server
Application Server
Custom
```

## 28. Configuration

`.env.example`:

```env
APP_ENV=development

DATABASE_URL=postgresql+psycopg://healthcheck:healthcheck@postgres:5432/healthcheck
REDIS_URL=redis://redis:6379/0

DATA_DIR=/data

SSH_CONNECT_TIMEOUT=10
SSH_COMMAND_TIMEOUT=60

WINRM_PORT=5985
WINRM_TRANSPORT=ntlm
WINRM_SERVER_CERT_VALIDATION=ignore
WINRM_TIMEOUT=30

CELERY_WORKER_CONCURRENCY=10

LOG_LEVEL=INFO

CORS_ORIGINS=http://localhost:3000
```

Never commit `.env`.

## 29. Docker Compose

Services:

```text
backend
worker
frontend
postgres
redis
```

Mount:

```text
./data:/data
```

## 30. Local Startup

The application must support:

```bash
git clone <repo>
cd migration-healthcheck
cp .env.example .env
docker compose up -d
```

Expected:

```text
Frontend: http://localhost:3000
API:      http://localhost:8000
Docs:     http://localhost:8000/docs
```

## 31. Logging

Use structured logging.

Every request:

```text
request_id
```

Every health check:

```text
run_id
server_id
```

Never log credentials.

## 32. Errors

Categorize:

```text
CONNECTION_ERROR
AUTHENTICATION_ERROR
TIMEOUT
COMMAND_ERROR
PARSER_ERROR
COLLECTOR_ERROR
STORAGE_ERROR
UNKNOWN_ERROR
```

Do not expose stack traces to normal users.

## 33. Concurrency

Use bounded Celery concurrency.

Example:

```env
CELERY_WORKER_CONCURRENCY=10
```

Do not create uncontrolled simultaneous SSH/WinRM connections.

## 34. Security

Implement:

- input validation
- CSV size limits
- file type validation
- path traversal protection
- command allowlisting
- timeouts
- secret protection
- secure API error responses
- no arbitrary shell commands from frontend
- audit logging

The frontend must never submit arbitrary commands to remote servers.

## 35. Mock Mode

Provide:

```env
MOCK_CONNECTORS=true
```

When enabled, Linux and Windows collectors return deterministic mock snapshots.

Provide at least:

```text
linux-web01
linux-db01
windows-app01
windows-db01
```

## 36. Seed Data

Provide:

```bash
python -m app.utils.seed
```

It should create:

- 10 mock servers
- PRE snapshots
- POST snapshots
- comparison results

## 37. Storage Abstraction

Create:

```python
class SnapshotStorage(ABC):
    async def save(...):
        ...
    async def load(...):
        ...
    async def delete(...):
        ...
```

MVP:

```text
LocalSnapshotStorage
```

Future:

```text
AzureBlobSnapshotStorage
```

Also abstract:

```python
CredentialProvider
```

Future provider:

```text
AzureKeyVaultCredentialProvider
```

## 38. Testing

Backend:

- CSV parser tests
- CSV validation tests
- Linux parser tests
- Windows parser tests
- comparison engine tests
- comparison rule tests
- storage tests
- API tests

Frontend:

- CSV upload
- dashboard
- server table
- health-check creation
- comparison rendering
- error states

E2E:

```text
Import CSV
  ↓
View servers
  ↓
Start health check
  ↓
View run
  ↓
View snapshot
  ↓
Create comparison
  ↓
View comparison
```

## 39. Development Sprints

### Sprint 0 — Bootstrap

Create:

- backend
- frontend
- PostgreSQL
- Redis
- Docker Compose
- environment configuration
- health endpoint
- CI
- README

Acceptance:

```bash
docker compose up -d
```

works.

### Sprint 1 — Server Inventory

Implement:

- database
- Server model
- CRUD API
- UI
- migrations

### Sprint 2 — CSV Import

Implement:

- upload
- validation
- preview
- duplicate detection
- import

### Sprint 3 — Connectors

Implement:

- BaseConnector
- SSHConnector
- WinRMConnector
- connection testing

### Sprint 4 — Linux Collector

Implement:

- OS
- CPU
- memory
- disk
- network
- services
- processes
- packages

### Sprint 5 — Windows Collector

Implement:

- OS
- CPU
- memory
- disk
- network
- services
- processes
- software

### Sprint 6 — Job Processing

Implement:

- Celery
- Redis
- worker
- queue
- progress
- cancellation

### Sprint 7 — Snapshot Storage

Implement:

- PRE
- POST
- raw JSON
- normalized JSON
- logs
- checksums

### Sprint 8 — Comparison

Implement:

- normalization
- comparison engine
- rules
- PASS/WARN/FAIL/INFO

### Sprint 9 — Comparison UI

Implement:

- side-by-side comparison
- changed-only
- failures-only
- warnings-only

### Sprint 10 — Dashboard

Implement:

- KPIs
- charts
- filters
- recent runs
- failure list

### Sprint 11 — Reports

Implement:

- JSON
- CSV
- HTML

Then add:

- Excel
- PDF

### Sprint 12 — Security

Implement:

- authentication
- RBAC
- credential encryption
- audit logs
- upload limits
- security headers
- rate limiting

### Sprint 13 — Azure Readiness

Implement storage/credential abstractions and Azure deployment documentation.

## 40. Definition of Done

For every sprint:

```text
Code implemented
Unit tests written
Integration tests where required
API tested
UI tested where applicable
Docker build successful
Documentation updated
No credentials committed
No broken existing tests
```

## 41. Final MVP Workflow

The completed MVP must support:

```text
CSV
 ↓
Import
 ↓
Linux / Windows detection
 ↓
SSH / WinRM
 ↓
PRE Health Check
 ↓
Snapshot
 ↓
Migration
 ↓
POST Health Check
 ↓
Snapshot
 ↓
Comparison
 ↓
PASS / WARN / FAIL / INFO
 ↓
Dashboard
 ↓
Report
```
