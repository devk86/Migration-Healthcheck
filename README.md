# Migration HealthCheck

Web platform for pre- and post-migration health checks on Linux and Windows servers.

```bash
cp .env.example .env
sudo docker compose up -d
```

| Surface | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8001 |
| Docs | http://localhost:8001/docs |

The API container listens on port 8000. This machine already uses host port 8000, so Compose publishes **8001**.

Lab sign-in is `admin` / `admin`. Change `ADMIN_PASSWORD` before any shared deployment. The Compose credential key and JWT secret are lab values, not production secrets.

Health checks use SSH and WinRM. Save a Linux or Windows credential, then run PRE and POST. Set `MOCK_CONNECTORS=true` only when you want generated snapshots instead of a live host.

## What you can do

1. Sign in.
2. Import a CSV with columns `Server name/IP,OS name`.
3. Save a server credential. The API never returns the secret.
4. Test the connection.
5. Run PRE, then POST.
6. Compare the snapshots and filter changes, failures, and warnings.
7. Read the dashboard.
8. Download JSON, CSV, HTML, Excel, or PDF.

## Local checks

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
ruff check app tests
pytest
```

```bash
cd frontend
npm ci
npm run lint
npm test
npm run build
```

Seed without Docker:

```bash
python -m app.utils.seed
```

## Layout

```text
backend/     FastAPI, collectors, comparison, Celery worker
frontend/    React application
data/        Logs, snapshots, comparisons, and reports
docs/        Architecture, API, collectors, and deployment
```
