import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class Server(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "servers"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    address: Mapped[str] = mapped_column(String(255), index=True)
    os_type: Mapped[str] = mapped_column(String(16), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    wave: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    last_pre_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_post_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_connection_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_connection_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    credentials: Mapped[list[Credential]] = relationship(
        back_populates="server",
        cascade="all, delete-orphan",
    )
    snapshots: Mapped[list[Snapshot]] = relationship(
        back_populates="server",
        cascade="all, delete-orphan",
    )
    results: Mapped[list[HealthCheckResult]] = relationship(
        back_populates="server",
        cascade="all, delete-orphan",
    )
    comparisons: Mapped[list[Comparison]] = relationship(
        back_populates="server",
        cascade="all, delete-orphan",
    )


class Credential(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "credentials"

    server_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("servers.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(32))
    username: Mapped[str] = mapped_column(String(255))
    secret_encrypted: Mapped[str] = mapped_column(String(8192))

    server: Mapped[Server] = relationship(back_populates="credentials")


class GlobalCredential(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "global_credentials"

    os_type: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(32))
    username: Mapped[str] = mapped_column(String(255))
    secret_encrypted: Mapped[str] = mapped_column(String(8192))
