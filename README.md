# Migration HealthCheck

Web platform for pre- and post-migration health checks on Linux and Windows servers. It collects a snapshot, keeps PRE and POST separate, compares them, and downloads reports.

Repository: https://github.com/devk86/Migration-Healthcheck

## Start the lab

```bash
cp .env.example .env
sudo docker compose up -d
```

| Surface | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8001 |
| Interactive API docs | http://localhost:8001/docs |

Sign in with `admin` / `admin`.

The API container listens on port 8000. Host port 8000 is already used on this machine, so Compose publishes **8001**. The frontend nginx proxies `/api` to the backend.

| Service | Host port | Role |
|---|---|---|
| frontend | 3000 | React build served by nginx |
| backend | 8001 | FastAPI |
| worker | none | Celery worker that runs health checks |
| postgres | 5432 | PostgreSQL 16 (`healthcheck` / `healthcheck`) |
| redis | 6379 | Redis 7 and the Celery broker |

`./data` is mounted at `/data` inside the backend and worker. Snapshots, raw command output, collector logs, comparison JSON, and generated reports are written there. Those files are gitignored. Only `.gitkeep` files are in the repository.

## Lab secrets

`docker-compose.yml` and `.env.example` contain lab-only values:

- login `admin` / `admin`
- JWT secret `lab-only-jwt-secret-change-me`
- Fernet key used to encrypt stored credentials

Change `ADMIN_PASSWORD`, `JWT_SECRET`, and `CREDENTIAL_KEY` before any shared or public deployment. The repository is public. Credentials already stored with the lab key cannot be read after the key changes.

## How a check runs

```text
Browser
  │
  ▼
React on nginx (:3000)
  │  /api
  ▼
FastAPI (:8001 → container :8000)
  │  creates a health-check run
  ▼
Celery worker
  │  SSH (Linux) or WinRM (Windows)
  ▼
Collector → immutable snapshot under /data
```

Server identity is the database id, not the IP address. PRE and POST are chosen explicitly. A finished snapshot file is not overwritten.

`MOCK_CONNECTORS` is `false`. A check connects to the real host. Set `MOCK_CONNECTORS=true` only when you want generated snapshots instead of a live connection. `SEED_ON_STARTUP` is `false`, so startup does not insert sample servers.

## Using the application

Pages: Dashboard, Servers, Import, Credentials, Runs, Reports.

1. Sign in.
2. Import servers from a CSV, or add one server at a time.
3. Save a Linux credential and a Windows credential on the Credentials page. One credential covers every server of that operating system. A credential saved on a single server overrides the shared one.
4. Run PRE before the migration.
5. Run POST after the migration.
6. Open Reports. The latest PRE, the latest POST, and a comparison are listed. The comparison is created from those two snapshots when you open Reports, and again when a POST check finishes.
7. Download the HTML file for PRE, POST, or the comparison. Generate also writes JSON, CSV, HTML, Excel, or PDF for a comparison.

A connection test and a health check use the same credential resolution: the server credential first, then the global credential for that operating system. The API never returns the password or private key.

## Servers and CSV import

Required headers, matched without case sensitivity:

```text
Server name/IP,OS name
192.168.0.201,linux
```

- `OS name` is `linux` or `windows`.
- The imported value is stored as both the server name and the address.
- Blank rows are skipped. A UTF-8 BOM is accepted.
- Columns named password, secret, private key, or credential are rejected.
- Preview does not save anything. Import is all or nothing: one bad row saves nothing.
- Importing a name that already exists returns an error for that row.

A sample file is `samples/servers.csv`.

## Credentials

| Operating system | Allowed kinds |
|---|---|
| Linux | `SSH_PASSWORD` or `SSH_PRIVATE_KEY` |
| Windows | `WINRM_PASSWORD` |

Secrets are encrypted with Fernet before they are stored. List responses include the username and kind only.

Linux SSH uses Paramiko. Host keys are accepted automatically in this lab. Windows uses WinRM (`pywinrm`), default port 5985, NTLM, with server certificate validation ignored.

This lab's OpenSSH listens on **port 2222**, so Compose sets `SSH_PORT=2222`. The application default is port 22. Set `SSH_PORT=22` before checking Linux hosts that use the standard port. `SSH_PORT` applies to every Linux server in the run.

## What a snapshot contains

Schema version `1.0`: `server`, `collection`, `os`, `cpu`, `memory`, `disk`, `network`, `services`, `processes`, `software`.

Linux collection uses a fixed allowlist: hostname, `/etc/os-release`, `uname`, `free`, `df`, `ip`, `ss`, `systemctl` (with `service --status-all` when needed), `ps`, and the full `dpkg-query` or `rpm -qa` package list. `tmpfs` and similar pseudo filesystems are skipped.

Windows collection uses CIM and PowerShell, one command per category, including adapters, routes, listening ports, services, processes, and installed software from both Uninstall registry keys.

The connector rejects any command that is not on the allowlist. The browser cannot send a command.

## Comparison rules

Comparison reads the two snapshots. It does not run collectors, and it does not compare packages or processes.

| Check | Result |
|---|---|
| CPU cores unchanged | PASS, otherwise WARN |
| Memory total change ≤ 5% | PASS |
| Memory total change ≤ 20% | WARN, otherwise FAIL |
| Disk usage change ≤ 5 percentage points | PASS |
| Disk usage change ≤ 10 percentage points | WARN, otherwise FAIL |
| Service running → running | PASS |
| Service running → stopped or absent | FAIL |
| Service stopped → running | INFO |
| IP address change | INFO |
| OS or hostname change | WARN |

Overall status uses this order: FAIL, ERROR, WARN, PASS, INFO, NOT_CHECKED.

## Reports

`GET /api/v1/reports/choices` returns, for each server:

- the latest PRE snapshot
- the latest POST snapshot
- a comparison when both exist

Download HTML:

- snapshot: `GET /api/v1/reports/snapshots/{snapshot_id}/html`
- comparison document `pre`, `post`, or `comparison`: `GET /api/v1/reports/documents/{comparison_id}/{document}`

Generate stores `json`, `csv`, `html`, `xlsx`, or `pdf` and is available for a comparison.

## API

Base path: `/api/v1`. Sign in with `POST /api/v1/auth/login` and send `Authorization: Bearer <token>`. The token is kept in the browser under `sessionStorage` key `mhc_token`. `GET /api/v1/health` is public and returns `ok` or `503` `degraded`.

Roles are `admin`, `operator`, and `viewer`. Viewers can read. Operators and admins can create servers, save credentials, and start checks.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Process, PostgreSQL, and Redis |
| POST | `/auth/login` | Issue a token |
| GET | `/auth/me` | Current user |
| GET, POST | `/servers` | List and create servers |
| GET, PATCH, DELETE | `/servers/{id}` | Read, update, delete |
| POST | `/servers/{id}/test-connection` | Test SSH or WinRM |
| GET, POST | `/servers/{id}/credentials` | Per-server credential; GET omits the secret |
| GET | `/servers/{id}/snapshots` | Snapshot metadata |
| GET | `/snapshots/{id}` | Normalized snapshot JSON |
| GET, PUT | `/credentials/global` and `/credentials/global/{os_type}` | Shared Linux and Windows credentials |
| POST | `/imports/servers` | Preview or import CSV |
| POST, GET | `/healthchecks` | Start and list runs |
| GET | `/healthchecks/{id}` | Run progress |
| POST | `/healthchecks/{id}/cancel` | Cancel a run |
| GET | `/healthchecks/{id}/results` | Per-server results |
| GET | `/healthchecks/{id}/logs` | Logs for a run |
| POST, GET | `/comparisons` | Create and list comparisons |
| GET | `/comparisons/{id}` | Comparison rows |
| GET | `/reports/choices` | PRE, POST, and comparison choices |
| POST, GET | `/reports` | Generate and list report files |
| GET | `/reports/{id}/download` | Download a generated file |
| GET | `/dashboard` | KPI and chart data |

Errors use `{ "detail": { "code", "message" } }` and do not include stack traces or submitted secrets.

Timestamps are UTC. Run states are `QUEUED`, `RUNNING`, `COMPLETED`, `PARTIAL`, `FAILED`, and `CANCELLED`.

## Configuration

Copy `.env.example`. Compose currently sets these on the backend and worker:

| Variable | Lab value | Meaning |
|---|---|---|
| `DATABASE_URL` | Postgres service | SQLAlchemy URL |
| `REDIS_URL` | Redis service | Celery broker |
| `DATA_DIR` | `/data` | Snapshot and report files |
| `MOCK_CONNECTORS` | `false` | Live SSH and WinRM |
| `SEED_ON_STARTUP` | `false` | Do not insert sample servers |
| `SSH_PORT` | `2222` | SSH port for every Linux server |
| `SSH_CONNECT_TIMEOUT` | `10` | Seconds |
| `SSH_COMMAND_TIMEOUT` | `60` | Seconds |
| `WINRM_PORT` | `5985` | WinRM port |
| `CELERY_EAGER` | `false` | Checks run on the worker, not inside the API process |
| `STORAGE_BACKEND` | `local` | Files under `DATA_DIR` |
| `CREDENTIAL_BACKEND` | `local` | Encrypted secrets in PostgreSQL |

`AzureBlobSnapshotStorage`, `AzureBlobLogStorage`, and `AzureKeyVaultCredentialProvider` exist and raise `NotImplementedError`. Local storage and the local credential provider are what run today.

## Local checks

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check app tests
pytest
```

Tests use SQLite and `MOCK_CONNECTORS=true`. They do not need Docker.

```bash
cd frontend
npm ci
npm run lint
npm test
npm run build
```

Seed sample servers without Docker, only when you want mock data:

```bash
python -m app.utils.seed
```

## Layout

```text
backend/     FastAPI, collectors, comparison, Celery worker
frontend/    React application
data/        Logs, snapshots, comparisons, and reports
docs/        Architecture, API, collectors, and deployment
samples/     Example server CSV
```

More detail is in `docs/architecture.md`, `docs/api.md`, `docs/collectors.md`, and `docs/deployment.md`.
