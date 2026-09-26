# Deployment

Local lab:

```bash
cp .env.example .env
sudo docker compose up -d
```

| Service | Host port | Role |
|---|---|---|
| frontend | 3000 | nginx and the React build |
| backend | 8001 | FastAPI, container port 8000 |
| worker | none | Celery health-check worker |
| postgres | 5432 | PostgreSQL 16 |
| redis | 6379 | Redis 7 and the Celery broker |

`./data` is mounted at `/data`.

The published API port is 8001 because host port 8000 is already taken on this machine.

## Azure later

Keep the same containers and point them at managed services:

- Azure Container Apps, or another container platform, for `backend`, `worker`, and `frontend`
- Azure Database for PostgreSQL (`DATABASE_URL`)
- Azure Cache for Redis (`REDIS_URL`)
- Azure Blob Storage behind `AzureBlobSnapshotStorage` and `AzureBlobLogStorage` (`STORAGE_BACKEND=azure`)
- Azure Key Vault behind `AzureKeyVaultCredentialProvider` (`CREDENTIAL_BACKEND=azure`)

Those Azure classes are not wired to a live account. Local storage and the local credential provider are the implementations that run today. Replace `CREDENTIAL_KEY`, `JWT_SECRET`, and `ADMIN_PASSWORD` before leaving the lab.
