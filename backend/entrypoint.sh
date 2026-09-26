#!/bin/sh
set -e
if [ -d /data ]; then
  chown -R appuser:appuser /data || true
fi
cd /app
su --preserve-environment appuser -s /bin/sh -c "alembic upgrade head && python -m app.utils.bootstrap"
exec su --preserve-environment appuser -s /bin/sh -c "exec uvicorn app.main:app --host 0.0.0.0 --port 8000"
