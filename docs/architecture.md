# Architecture

```text
Browser
  │
  ▼
React on nginx (:3000)
  │  /api
  ▼
FastAPI (container :8000, host :8001)
  ├── PostgreSQL
  ├── Redis / Celery worker
  └── local files under /data
```

Routes enqueue a health-check run. The Celery worker connects with SSH or WinRM, or with the mock connector when `MOCK_CONNECTORS=true`. Collectors normalize command output. Comparison rules read those snapshots and do not live inside the collectors.

Server identity is the database id. PRE and POST are chosen explicitly. A completed snapshot file is not overwritten.

Credentials are encrypted with Fernet before they are stored. GET responses omit secrets. Logs store command text, stdout, stderr, and exit codes for allowlisted commands only.

`SnapshotStorage`, `LogStorage`, and `CredentialProvider` have local implementations. The Azure Blob and Key Vault classes are present and raise until those services are configured.
