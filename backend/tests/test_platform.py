from pathlib import Path

import pytest
from app.collectors.linux.disk import parse_disk
from app.collectors.linux.os import parse_os_release
from app.collectors.windows.memory import parse_memory
from app.comparison.engine import compare
from app.connectors.ssh import SSHConnector
from app.errors import CommandFailed, StorageFailed
from app.utils.filesystem import safe_path
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_server_crud_and_filter(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/servers",
        headers=auth_headers,
        json={"name": "web01", "address": "192.168.1.20", "os_type": "Linux", "wave": "wave-1"},
    )
    assert created.status_code == 201
    server_id = created.json()["id"]
    assert created.json()["os_type"] == "linux"

    listed = await client.get("/api/v1/servers", headers=auth_headers, params={"os_type": "linux", "q": "web"})
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = await client.patch(
        f"/api/v1/servers/{server_id}",
        headers=auth_headers,
        json={"address": "10.0.0.5"},
    )
    assert updated.status_code == 200
    assert updated.json()["address"] == "10.0.0.5"

    invalid = await client.post(
        "/api/v1/servers",
        headers=auth_headers,
        json={"name": "bad", "address": "1.1.1.1", "os_type": "solaris"},
    )
    assert invalid.status_code == 422

    deleted = await client.delete(f"/api/v1/servers/{server_id}", headers=auth_headers)
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_csv_import_rejects_bad_rows_without_partial_create(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    content = b"Server name/IP,OS name\nweb01,linux\n,windows\nwin01,solaris\nweb01,Linux\n"
    preview = await client.post(
        "/api/v1/imports/servers",
        headers=auth_headers,
        files={"file": ("servers.csv", content, "text/csv")},
        data={"mode": "import"},
    )
    assert preview.status_code == 200
    body = preview.json()
    assert body["imported"] == 0
    assert body["errors"]
    listed = await client.get("/api/v1/servers", headers=auth_headers)
    assert listed.json() == []

    good = b"Server name/IP,OS name\nweb01,linux\nwin01,WINDOWS\n"
    imported = await client.post(
        "/api/v1/imports/servers",
        headers=auth_headers,
        files={"file": ("servers.csv", good, "text/csv")},
        data={"mode": "import"},
    )
    assert imported.status_code == 200
    assert imported.json()["imported"] == 2

    bom = b"\xef\xbb\xbfServer name/IP,OS name\nweb02,linux\n\n"
    with_blank = await client.post(
        "/api/v1/imports/servers",
        headers=auth_headers,
        files={"file": ("servers.csv", bom, "text/csv")},
        data={"mode": "import"},
    )
    assert with_blank.status_code == 200
    assert with_blank.json()["imported"] == 1
    assert with_blank.json()["errors"] == []


@pytest.mark.asyncio
async def test_credential_secret_is_not_returned(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    created = await client.post(
        "/api/v1/servers",
        headers=auth_headers,
        json={"name": "web01", "address": "web01", "os_type": "linux"},
    )
    server_id = created.json()["id"]
    saved = await client.post(
        f"/api/v1/servers/{server_id}/credentials",
        headers=auth_headers,
        json={"kind": "SSH_PASSWORD", "username": "root", "secret": "super-secret"},
    )
    assert saved.status_code == 201
    assert "super-secret" not in saved.text
    listed = await client.get(f"/api/v1/servers/{server_id}/credentials", headers=auth_headers)
    assert listed.json()[0]["username"] == "root"
    assert "secret" not in listed.json()[0]


@pytest.mark.asyncio
async def test_global_credential_covers_servers_without_their_own(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    saved = await client.put(
        "/api/v1/credentials/global/linux",
        headers=auth_headers,
        json={"kind": "SSH_PASSWORD", "username": "root", "secret": "shared-secret"},
    )
    assert saved.status_code == 200
    assert "shared-secret" not in saved.text
    listed = await client.get("/api/v1/credentials/global", headers=auth_headers)
    assert listed.json()[0]["username"] == "root"
    assert "secret" not in listed.json()[0]

    mismatch = await client.put(
        "/api/v1/credentials/global/linux",
        headers=auth_headers,
        json={"kind": "WINRM_PASSWORD", "username": "root", "secret": "shared-secret"},
    )
    assert mismatch.status_code == 422

    created = await client.post(
        "/api/v1/servers",
        headers=auth_headers,
        json={"name": "linux-shared", "address": "linux-shared", "os_type": "linux"},
    )
    server_id = created.json()["id"]
    run = await client.post(
        "/api/v1/healthchecks",
        headers=auth_headers,
        json={"server_ids": [server_id], "phase": "PRE"},
    )
    assert run.status_code == 201
    detail = await client.get(f"/api/v1/healthchecks/{run.json()['id']}", headers=auth_headers)
    assert detail.json()["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_report_choices_include_pre_snapshot_without_comparison(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    created = await client.post(
        "/api/v1/servers",
        headers=auth_headers,
        json={"name": "csv-host", "address": "csv-host", "os_type": "linux"},
    )
    server_id = created.json()["id"]
    await client.post(
        f"/api/v1/servers/{server_id}/credentials",
        headers=auth_headers,
        json={"kind": "SSH_PASSWORD", "username": "root", "secret": "mock-not-used"},
    )
    run = await client.post(
        "/api/v1/healthchecks",
        headers=auth_headers,
        json={"server_ids": [server_id], "phase": "PRE"},
    )
    assert run.status_code == 201
    choices = await client.get("/api/v1/reports/choices", headers=auth_headers)
    assert choices.status_code == 200
    host = [item for item in choices.json() if item["server_name"] == "csv-host"]
    assert [item["kind"] for item in host] == ["pre"]
    html = await client.get(f"/api/v1/reports/snapshots/{host[0]['snapshot_id']}/html", headers=auth_headers)
    assert html.status_code == 200
    assert "csv-host-pre.html" in html.headers["content-disposition"]
    assert "csv-host" in html.text


@pytest.mark.asyncio
async def test_mock_healthcheck_comparison_and_report(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    created = await client.post(
        "/api/v1/servers",
        headers=auth_headers,
        json={"name": "linux-web01", "address": "linux-web01", "os_type": "linux"},
    )
    server_id = created.json()["id"]
    await client.post(
        f"/api/v1/servers/{server_id}/credentials",
        headers=auth_headers,
        json={"kind": "SSH_PASSWORD", "username": "root", "secret": "mock-not-used"},
    )
    for phase in ("PRE", "POST"):
        run = await client.post(
            "/api/v1/healthchecks",
            headers=auth_headers,
            json={"server_ids": [server_id], "phase": phase},
        )
        assert run.status_code == 201
        assert run.json()["status"] == "COMPLETED"
    snapshots = await client.get(f"/api/v1/servers/{server_id}/snapshots", headers=auth_headers)
    by_phase = {item["phase"]: item["id"] for item in snapshots.json()}
    comparison = await client.post(
        "/api/v1/comparisons",
        headers=auth_headers,
        json={"pre_snapshot_id": by_phase["PRE"], "post_snapshot_id": by_phase["POST"]},
    )
    assert comparison.status_code == 201
    body = comparison.json()
    assert body["overall_status"] == "WARN"
    disk = next(row for row in body["results"] if row["category"] == "disk")
    assert disk["status"] == "WARN"
    report = await client.post(
        "/api/v1/reports",
        headers=auth_headers,
        json={"comparison_id": body["id"], "format": "json"},
    )
    assert report.status_code == 201
    downloaded = await client.get(f"/api/v1/reports/{report.json()['id']}/download", headers=auth_headers)
    assert downloaded.status_code == 200
    assert "linux-web01" in downloaded.text
    for document in ("pre", "post", "comparison"):
        html = await client.get(
            f"/api/v1/reports/documents/{body['id']}/{document}",
            headers=auth_headers,
        )
        assert html.status_code == 200
        assert "text/html" in html.headers["content-type"]
        assert f"linux-web01-{document}.html" in html.headers["content-disposition"]
        assert "linux-web01" in html.text
    rejected = await client.get(f"/api/v1/reports/documents/{body['id']}/raw", headers=auth_headers)
    assert rejected.status_code == 422


@pytest.mark.asyncio
async def test_pre_and_post_make_comparison_report_available(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    created = await client.post(
        "/api/v1/servers",
        headers=auth_headers,
        json={"name": "compare-host", "address": "compare-host", "os_type": "linux"},
    )
    server_id = created.json()["id"]
    await client.post(
        f"/api/v1/servers/{server_id}/credentials",
        headers=auth_headers,
        json={"kind": "SSH_PASSWORD", "username": "root", "secret": "mock-not-used"},
    )
    for phase in ("PRE", "POST"):
        run = await client.post(
            "/api/v1/healthchecks",
            headers=auth_headers,
            json={"server_ids": [server_id], "phase": phase},
        )
        assert run.status_code == 201
        assert run.json()["status"] == "COMPLETED"
    choices = await client.get("/api/v1/reports/choices", headers=auth_headers)
    host = [item for item in choices.json() if item["server_name"] == "compare-host"]
    comparison = next(item for item in host if item["kind"] == "comparison")
    assert comparison["comparison_id"]
    html = await client.get(
        f"/api/v1/reports/documents/{comparison['comparison_id']}/comparison",
        headers=auth_headers,
    )
    assert html.status_code == 200
    assert "compare-host" in html.text


def test_package_and_network_collection_keeps_every_row() -> None:
    from app.collectors.linux.packages import parse_packages
    from app.collectors.windows.network import parse_network

    packages = parse_packages("MANAGER=apt\nnginx\t1.24.0\nopenssh-server\t1:9.6\n")
    assert packages["count"] == 2
    assert len(packages["packages"]) == 2
    network = parse_network(
        '{"adapters":[{"Description":"Ethernet","IPAddress":["10.0.0.5"],'
        '"MACAddress":"aa","DefaultIPGateway":["10.0.0.1"],"DNSServerSearchOrder":["1.1.1.1"]}],'
        '"routes":[{"DestinationPrefix":"0.0.0.0/0","NextHop":"10.0.0.1"}],"ports":[22,443]}'
    )
    assert network["listening_ports"] == [22, 443]
    assert network["routes"] == ["0.0.0.0/0 via 10.0.0.1"]


def test_linux_and_windows_parsers() -> None:
    parsed = parse_os_release('NAME="Ubuntu"\nVERSION_ID="24.04"\n')
    assert parsed["distribution"] == "Ubuntu"
    disk = parse_disk(
        "Filesystem Type 1024-blocks Used Available Capacity Mounted on\n"
        "/dev/sda1 ext4 100 62 38 62% /\n"
        "tmpfs tmpfs 10 0 10 0% /dev/shm\n"
    )
    assert disk["volumes"][0]["mount"] == "/"
    assert all(item["filesystem"] != "tmpfs" for item in disk["volumes"])
    memory = parse_memory('{"TotalVisibleMemorySize": 1024, "FreePhysicalMemory": 256}')
    assert memory["total"] == 1024 * 1024


def test_comparison_rules() -> None:
    pre = {
        "cpu": {"cores": 4},
        "memory": {"total": 32 * 1024**3},
        "disk": {"volumes": [{"mount": "/", "usage_percent": 62}]},
        "services": {"items": [{"name": "nginx", "status": "running"}, {"name": "postgres", "status": "running"}]},
        "os": {"hostname": "web01", "distribution": "Ubuntu", "distribution_version": "24.04"},
        "network": {"interfaces": [{"name": "eth0", "addresses": ["192.168.1.20"]}]},
    }
    post = {
        "cpu": {"cores": 8},
        "memory": {"total": 16 * 1024**3},
        "disk": {"volumes": [{"mount": "/", "usage_percent": 80}]},
        "services": {"items": [{"name": "nginx", "status": "running"}, {"name": "postgres", "status": "stopped"}]},
        "os": {"hostname": "web01-new", "distribution": "Ubuntu", "distribution_version": "22.04"},
        "network": {"interfaces": [{"name": "eth0", "addresses": ["10.0.0.8"]}]},
    }
    outcome = compare(pre, post)
    statuses = {row["category"]: row["status"] for row in outcome["categories"]}
    assert statuses["cpu"] == "WARN"
    assert statuses["memory"] == "FAIL"
    assert statuses["hostname"] == "WARN"
    assert statuses["os"] == "WARN"
    assert statuses["ip"] == "INFO"
    assert outcome["overall_status"] == "FAIL"


def test_storage_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(StorageFailed):
        safe_path(tmp_path, "..", "etc")


@pytest.mark.asyncio
async def test_ssh_rejects_arbitrary_command() -> None:
    connector = SSHConnector(host="localhost", username="root", password="secret")
    with pytest.raises(CommandFailed):
        await connector.execute("rm -rf /")


@pytest.mark.asyncio
async def test_login_required(client: AsyncClient) -> None:
    response = await client.get("/api/v1/servers")
    assert response.status_code == 401
    assert "password" not in response.text
