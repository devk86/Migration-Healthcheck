from sqlalchemy.orm import Session

from app.models import AuditLog


def record(session: Session, actor: str, action: str, target: str, detail: str = "") -> None:
    session.add(AuditLog(actor=actor, action=action, target=target, detail=detail[:500]))
