import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import NotFoundError, ValidationFailed
from app.models import Credential, GlobalCredential, Server
from app.security.crypto import encrypt_secret
from app.services.audit import record

KINDS = {"SSH_PASSWORD", "SSH_PRIVATE_KEY", "WINRM_PASSWORD"}
OS_KINDS = {
    "linux": {"SSH_PASSWORD", "SSH_PRIVATE_KEY"},
    "windows": {"WINRM_PASSWORD"},
}


def set_credential(
    session: Session,
    server_id: uuid.UUID,
    *,
    kind: str,
    username: str,
    secret: str,
    actor: str,
) -> Credential:
    if kind not in KINDS:
        raise ValidationFailed("Credential type is not supported.")
    if not username.strip() or not secret.strip():
        raise ValidationFailed("Username and secret are required.")
    server = session.get(Server, server_id)
    if server is None:
        raise NotFoundError("Server was not found.")
    credential = session.scalar(
        select(Credential).where(Credential.server_id == server_id, Credential.kind == kind)
    )
    encrypted = encrypt_secret(secret)
    if credential is None:
        credential = Credential(
            server_id=server_id,
            kind=kind,
            username=username.strip(),
            secret_encrypted=encrypted,
        )
        session.add(credential)
    else:
        credential.username = username.strip()
        credential.secret_encrypted = encrypted
    record(session, actor, "credential.set", f"{server.name}:{kind}")
    session.commit()
    session.refresh(credential)
    return credential


def list_credentials(session: Session, server_id: uuid.UUID) -> list[Credential]:
    if session.get(Server, server_id) is None:
        raise NotFoundError("Server was not found.")
    return list(
        session.scalars(select(Credential).where(Credential.server_id == server_id).order_by(Credential.kind))
    )


@dataclass(frozen=True)
class ResolvedCredential:
    username: str
    secret_encrypted: str
    kind: str


def set_global_credential(
    session: Session,
    os_type: str,
    *,
    kind: str,
    username: str,
    secret: str,
    actor: str,
) -> GlobalCredential:
    allowed = OS_KINDS.get(os_type)
    if allowed is None:
        raise ValidationFailed("OS must be linux or windows.")
    if kind not in allowed:
        raise ValidationFailed("Credential type does not match the operating system.")
    if not username.strip() or not secret.strip():
        raise ValidationFailed("Username and secret are required.")
    credential = session.scalar(select(GlobalCredential).where(GlobalCredential.os_type == os_type))
    encrypted = encrypt_secret(secret)
    if credential is None:
        credential = GlobalCredential(
            os_type=os_type,
            kind=kind,
            username=username.strip(),
            secret_encrypted=encrypted,
        )
        session.add(credential)
    else:
        credential.kind = kind
        credential.username = username.strip()
        credential.secret_encrypted = encrypted
    record(session, actor, "credential.global.set", os_type)
    session.commit()
    session.refresh(credential)
    return credential


def list_global_credentials(session: Session) -> list[GlobalCredential]:
    return list(session.scalars(select(GlobalCredential).order_by(GlobalCredential.os_type)))


def resolve_credential(session: Session, server: Server) -> ResolvedCredential | None:
    kinds = ["WINRM_PASSWORD"] if server.os_type == "windows" else ["SSH_PRIVATE_KEY", "SSH_PASSWORD"]
    for kind in kinds:
        credential = session.scalar(
            select(Credential).where(Credential.server_id == server.id, Credential.kind == kind)
        )
        if credential is not None:
            return ResolvedCredential(credential.username, credential.secret_encrypted, credential.kind)
    shared = session.scalar(select(GlobalCredential).where(GlobalCredential.os_type == server.os_type))
    if shared is None or shared.kind not in kinds:
        return None
    return ResolvedCredential(shared.username, shared.secret_encrypted, shared.kind)
