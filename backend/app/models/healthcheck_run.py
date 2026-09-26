import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey, utcnow


class HealthCheckRun(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "healthcheck_runs"

    phase: Mapped[str] = mapped_column(String(8), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True, default="QUEUED")
    server_ids: Mapped[list[str]] = mapped_column(JSON)
    created_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[int] = mapped_column(Integer, default=0)
    running_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    queued_count: Mapped[int] = mapped_column(Integer, default=0)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)

    results: Mapped[list[HealthCheckResult]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class HealthCheckResult(UUIDPrimaryKey, Base):
    __tablename__ = "healthcheck_results"

    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("healthcheck_runs.id", ondelete="CASCADE"))
    server_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("servers.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(16))
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    snapshot_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    run: Mapped[HealthCheckRun] = relationship(back_populates="results")
    server: Mapped[Server] = relationship(back_populates="results")
