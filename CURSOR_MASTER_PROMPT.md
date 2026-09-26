# Cursor Master Implementation Prompt

You are implementing a production-quality web application called:

**Migration HealthCheck & Comparison Platform**

The platform performs standardized pre- and post-migration health checks against Linux and Windows servers and compares the results.

## Source of truth

Read and follow:

```text
PROJECT_SPEC.md
```

Do not redesign the architecture unless there is a strong technical reason. If a change is necessary, document the reason in the implementation summary.

## Technology

### Backend

- Python 3.14+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic v2
- PostgreSQL
- Redis
- Celery
- Paramiko
- pywinrm
- pandas

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

# Critical Architecture Rules

1. Do not put SSH/WinRM logic inside FastAPI routes.
2. Do not put comparison logic inside collectors.
3. Never expose credentials through normal API responses.
4. Never write passwords, private keys, tokens, or other secrets to logs.
5. Never allow arbitrary shell commands from the frontend.
6. Use bounded background concurrency.
7. PRE and POST snapshots must be immutable.
8. Preserve raw and normalized collector output.
9. Use database server ID as the server identity, not IP address.
10. Abstract storage so local filesystem storage can later be replaced by Azure Blob Storage.
11. Abstract credential storage so local storage can later be replaced by Azure Key Vault.
12. All APIs must use `/api/v1/`.
13. Use UTC internally for timestamps.
14. Use UUIDs for health-check runs and comparisons.
15. Write tests for every parser and comparison rule.
16. Avoid giant files and duplicated Linux/Windows business logic.
17. Use type hints throughout the backend.
18. Use clear exception classes and structured logging.
19. Keep collectors independently testable.
20. Do not claim a feature is complete unless it is implemented, tested, and accessible from the UI.

# Implementation Order

Implement one sprint at a time.

Do not implement future sprints unless explicitly requested.

After each sprint:

1. Run backend tests.
2. Run frontend tests.
3. Run linting.
4. Run type checking.
5. Build Docker images.
6. Verify Docker Compose.
7. Update documentation.
8. Fix all failures before proceeding.

# Sprint 0 — Project Bootstrap

Create:

- backend
- frontend
- PostgreSQL
- Redis
- Docker Compose
- environment configuration
- health endpoint
- README
- `.gitignore`
- initial tests
- basic CI configuration

Verify:

```bash
docker compose up -d
```

Expected:

```text
Frontend: http://localhost:3000
API:      http://localhost:8000
Docs:     http://localhost:8000/docs
```

Do not implement collectors yet.

# Sprint 1 — Database and Server Inventory

Implement:

- SQLAlchemy models
- Alembic migrations
- Server model
- Server CRUD
- API schemas
- service layer
- repository layer where appropriate
- frontend server table
- server details page

Required fields:

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

Test:

- create
- read
- update
- delete
- filter
- validation

# Sprint 2 — CSV Import

Required CSV:

```csv
Server name/IP,OS name
web01,linux
win01,windows
```

Implement:

- upload
- validation
- preview
- duplicate detection
- invalid OS detection
- import
- row-level error reporting

Accepted OS values are case-insensitive:

```text
linux
windows
```

Do not support credentials in CSV.

# Sprint 3 — Connector Framework

Implement:

```python
BaseConnector
SSHConnector
WinRMConnector
```

Support:

- connection timeout
- command timeout
- authentication errors
- unreachable server
- clean disconnect
- test connection API

SSH uses Paramiko.

Windows uses pywinrm.

Never log credentials.

# Sprint 4 — Linux Collector

Implement:

- OS
- CPU
- memory
- disk
- network
- services
- processes
- packages

Implement a common normalized snapshot format.

Handle different Linux distributions gracefully.

Do not assume systemd exists.

Test all parsers using fixtures.

# Sprint 5 — Windows Collector

Implement:

- OS
- CPU
- memory
- disk
- network
- services
- processes
- software

Use PowerShell/CIM where appropriate.

Test parsers using fixtures.

# Sprint 6 — Background Jobs

Implement:

- Celery
- Redis
- health-check task
- run lifecycle
- progress tracking
- bounded concurrency
- cancellation

Run states:

```text
QUEUED
RUNNING
COMPLETED
PARTIAL
FAILED
CANCELLED
```

# Sprint 7 — Snapshot and Log Storage

Implement:

```text
data/logs/
data/snapshots/
data/comparisons/
data/reports/
```

Store:

- raw command output
- normalized JSON
- collector logs
- checksums

Create storage interfaces so local storage can later be replaced by Azure storage.

# Sprint 8 — PRE/POST Comparison Engine

Implement:

```python
compare(pre_snapshot, post_snapshot, rules)
```

Default statuses:

```text
PASS
WARN
FAIL
INFO
NOT_CHECKED
ERROR
```

Implement deterministic comparison rules for:

- CPU
- memory
- disk
- services
- OS
- hostname
- IP address

IP changes should normally be informational.

All comparison rules must have unit tests.

# Sprint 9 — Comparison UI

Implement:

- PRE vs POST side-by-side view
- category comparison
- changed-only filter
- failure filter
- warning filter
- overall status
- detailed differences

# Sprint 10 — Dashboard

Implement:

- total servers
- PRE completed
- POST completed
- pass count
- warning count
- failure count
- connection errors
- recent health-check runs
- failures by category
- OS distribution
- PRE vs POST charts
- filters

# Sprint 11 — Reports

Implement:

- JSON
- CSV
- HTML

Then implement:

- Excel
- PDF

Reports must contain:

- server
- OS
- PRE timestamp
- POST timestamp
- overall result
- category results
- changed metrics
- warnings
- failures

# Sprint 12 — Security

Implement:

- authentication
- authorization/RBAC
- encrypted credential storage
- audit logging
- upload size limits
- file validation
- path traversal protection
- secure headers
- rate limiting
- safe error responses

Never allow arbitrary remote command execution.

# Sprint 13 — Azure Readiness

Implement/document:

```text
SnapshotStorage
LogStorage
CredentialProvider
```

Local implementations:

```text
LocalSnapshotStorage
LocalLogStorage
LocalCredentialProvider
```

Document future implementations:

```text
AzureBlobSnapshotStorage
AzureBlobLogStorage
AzureKeyVaultCredentialProvider
```

Document deployment to:

- Azure Container Apps or equivalent container platform
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Azure Blob Storage
- Azure Key Vault

# Mock Development Mode

Support:

```env
MOCK_CONNECTORS=true
```

When enabled, provide deterministic Linux and Windows snapshots without connecting to real servers.

Provide seed data:

```bash
python -m app.utils.seed
```

Create:

- 10 mock servers
- PRE snapshots
- POST snapshots
- comparison results

This is required for frontend development and CI.

# Required Final User Workflow

A user must eventually be able to:

1. Start the application using Docker Compose.
2. Upload the CSV.
3. Preview and validate the CSV.
4. Import Linux and Windows servers.
5. Configure credentials.
6. Test connectivity.
7. Select servers.
8. Select PRE or POST.
9. Start a health-check run.
10. Watch progress.
11. View results.
12. View logs.
13. View immutable snapshots.
14. Select PRE and POST snapshots.
15. Generate a comparison.
16. See PASS/WARN/FAIL/INFO.
17. Filter changed metrics.
18. View the migration dashboard.
19. Generate/download reports.

# Required Documentation

Maintain:

```text
README.md
docs/architecture.md
docs/api.md
docs/collectors.md
docs/deployment.md
```

Documentation must match the actual implementation.

# Completion Rule

Do not report "complete" merely because files were generated.

A sprint is complete only when:

- implementation exists
- tests pass
- Docker builds
- services start
- documented commands work
- frontend can reach backend
- relevant UI functionality is usable
- no credentials are exposed
- existing tests continue to pass

At the end of each sprint, provide:

1. Files created.
2. Files modified.
3. Features implemented.
4. Tests executed.
5. Test results.
6. Docker verification result.
7. Known limitations.
8. Exact command to proceed to the next sprint.
