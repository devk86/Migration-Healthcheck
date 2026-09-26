import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client


@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.health.probe_database", lambda: "ok")
    monkeypatch.setattr("app.api.health.probe_redis", lambda: "ok")

    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "migration-healthcheck"
    assert body["checks"] == {"database": "ok", "redis": "ok"}
    assert response.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_health_preserves_incoming_request_id(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.api.health.probe_database", lambda: "ok")
    monkeypatch.setattr("app.api.health.probe_redis", lambda: "ok")

    response = await client.get("/api/v1/health", headers={"X-Request-ID": "req-123"})

    assert response.headers["X-Request-ID"] == "req-123"


@pytest.mark.asyncio
async def test_health_degraded_when_database_fails(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.api.health.probe_database", lambda: "error")
    monkeypatch.setattr("app.api.health.probe_redis", lambda: "ok")

    response = await client.get("/api/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == "error"
    assert "password" not in response.text
    assert "healthcheck:" not in response.text
