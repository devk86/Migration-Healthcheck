import uuid

from app.models import Server
from sqlalchemy import or_, select
from sqlalchemy.orm import Session


def list_servers(
    session: Session,
    *,
    os_type: str | None = None,
    enabled: bool | None = None,
    wave: str | None = None,
    query: str | None = None,
) -> list[Server]:
    stmt = select(Server).order_by(Server.name)
    if os_type:
        stmt = stmt.where(Server.os_type == os_type.lower())
    if enabled is not None:
        stmt = stmt.where(Server.enabled == enabled)
    if wave:
        stmt = stmt.where(Server.wave == wave)
    if query:
        pattern = f"%{query.lower()}%"
        stmt = stmt.where(
            or_(Server.name.ilike(pattern), Server.address.ilike(pattern)),
        )
    return list(session.scalars(stmt))


def get_server(session: Session, server_id: uuid.UUID) -> Server | None:
    return session.get(Server, server_id)
