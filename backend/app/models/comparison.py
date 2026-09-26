import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKey, utcnow


class Comparison(UUIDPrimaryKey, Base):
    __tablename__ = "comparisons"

    server_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("servers.id", ondelete="CASCADE"), index=True)
    pre_snapshot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("snapshots.id", ondelete="CASCADE"))
    post_snapshot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("snapshots.id", ondelete="CASCADE"))
    overall_status: Mapped[str] = mapped_column(String(16), index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    server: Mapped[Server] = relationship(back_populates="comparisons")
    results: Mapped[list[ComparisonResult]] = relationship(
        back_populates="comparison",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list[Report]] = relationship(
        back_populates="comparison",
        cascade="all, delete-orphan",
    )


class ComparisonResult(UUIDPrimaryKey, Base):
    __tablename__ = "comparison_results"

    comparison_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("comparisons.id", ondelete="CASCADE"),
        index=True,
    )
    category: Mapped[str] = mapped_column(String(32))
    metric: Mapped[str] = mapped_column(String(255))
    pre_value: Mapped[str] = mapped_column(String(1024))
    post_value: Mapped[str] = mapped_column(String(1024))
    change: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), index=True)
    changed: Mapped[bool] = mapped_column(Boolean, default=False)

    comparison: Mapped[Comparison] = relationship(back_populates="results")
