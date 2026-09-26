# API

Base path: `/api/v1`

Interactive docs: `http://localhost:8001/docs`

Sign in with `POST /api/v1/auth/login`. Send `Authorization: Bearer <token>` on later calls. `GET /api/v1/health` stays public.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Process, PostgreSQL, and Redis |
| POST | `/auth/login` | Issue a token |
| GET | `/auth/me` | Current user |
| GET, POST | `/servers` | List and create servers |
| GET, PATCH, DELETE | `/servers/{id}` | Read, update, delete |
| POST | `/servers/{id}/test-connection` | Test SSH or WinRM |
| GET, POST | `/servers/{id}/credentials` | Metadata only on read |
| GET | `/servers/{id}/snapshots` | Snapshot metadata |
| GET | `/servers/{id}/logs` | Collector logs |
| GET | `/snapshots/{id}` | Normalized snapshot JSON |
| POST | `/imports/servers` | Preview or import CSV |
| POST, GET | `/healthchecks` | Start and list runs |
| GET | `/healthchecks/{id}` | Run progress |
| POST | `/healthchecks/{id}/cancel` | Cancel a run |
| GET | `/healthchecks/{id}/results` | Per-server results |
| GET | `/healthchecks/{id}/logs` | Logs for a run |
| POST, GET | `/comparisons` | Create and list comparisons |
| GET | `/comparisons/{id}` | Comparison rows |
| POST, GET | `/reports` | Create and list reports |
| GET | `/reports/{id}` | Report metadata |
| GET | `/reports/{id}/download` | Report file |
| GET | `/dashboard` | KPI and chart data |

Errors use `{ "detail": { "code", "message" } }` and do not include stack traces.
