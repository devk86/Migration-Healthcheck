import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["APP_ENV"] = "test"
os.environ["CREDENTIAL_KEY"] = "_iwmMUD3UBicRWWSkwGosyXUBwNvy62qJgKNVJbKvKQ="
os.environ["JWT_SECRET"] = "test-secret-test-secret-test-secret"
os.environ["MOCK_CONNECTORS"] = "true"
os.environ["CELERY_EAGER"] = "true"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "admin"
os.environ["SEED_ON_STARTUP"] = "false"

import pytest
from app.config import get_settings
from app.database.database import get_engine, reset_database
from app.models import Base
from app.utils.bootstrap import ensure_admin
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def fresh_database(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    reset_database()
    Base.metadata.create_all(get_engine())
    ensure_admin()
    yield
    reset_database()
    get_settings.cache_clear()


@pytest.fixture
async def client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    response = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
