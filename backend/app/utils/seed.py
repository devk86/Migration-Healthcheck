import uuid

from sqlalchemy import func, select

from app.database.database import get_sessionmaker
from app.models import Comparison, Credential, Server, Snapshot
from app.security.crypto import encrypt_secret
from app.services.comparison_service import create_comparison
from app.services.healthcheck_service import create_run, execute_run
from app.utils.bootstrap import ensure_admin

SERVERS = [
    ("linux-web01", "linux", "wave-1"),
    ("linux-db01", "linux", "wave-1"),
    ("linux-app01", "linux", "wave-1"),
    ("linux-cache01", "linux", "wave-1"),
    ("linux-mq01", "linux", "wave-1"),
    ("windows-app01", "windows", "wave-2"),
    ("windows-db01", "windows", "wave-2"),
    ("windows-file01", "windows", "wave-2"),
    ("windows-web01", "windows", "wave-2"),
    ("windows-dc01", "windows", "wave-2"),
]


def seed_if_empty() -> None:
    ensure_admin()
    session = get_sessionmaker()()
    try:
        count = session.scalar(select(func.count()).select_from(Server)) or 0
        if count:
            return
        ids: list[uuid.UUID] = []
        for name, os_type, wave in SERVERS:
            server = Server(name=name, address=name, os_type=os_type, enabled=True, wave=wave)
            session.add(server)
            session.flush()
            kind = "WINRM_PASSWORD" if os_type == "windows" else "SSH_PASSWORD"
            session.add(
                Credential(
                    server_id=server.id,
                    kind=kind,
                    username="mock",
                    secret_encrypted=encrypt_secret("mock-not-used"),
                )
            )
            ids.append(server.id)
        session.commit()
        server_ids = list(ids)
    finally:
        session.close()

    for phase in ("PRE", "POST"):
        session = get_sessionmaker()()
        try:
            run = create_run(
                session,
                server_ids=server_ids,
                phase=phase,
                actor="seed",
                user_id=None,
                enqueue=False,
            )
            run_id = str(run.id)
        finally:
            session.close()
        execute_run(run_id)

    session = get_sessionmaker()()
    try:
        import asyncio

        for server_id in server_ids:
            pre = session.scalar(
                select(Snapshot).where(Snapshot.server_id == server_id, Snapshot.phase == "PRE")
            )
            post = session.scalar(
                select(Snapshot).where(Snapshot.server_id == server_id, Snapshot.phase == "POST")
            )
            if pre is None or post is None:
                continue
            existing = session.scalar(select(Comparison).where(Comparison.server_id == server_id))
            if existing is not None:
                continue
            asyncio.run(
                create_comparison(
                    session,
                    pre_snapshot_id=pre.id,
                    post_snapshot_id=post.id,
                    actor="seed",
                    user_id=None,
                )
            )
    finally:
        session.close()


def main() -> None:
    seed_if_empty()


if __name__ == "__main__":
    main()
