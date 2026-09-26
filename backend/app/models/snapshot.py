import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKey, utcnow


class Snapshot(UUIDPrimaryKey, Base):
    __tablename__ = "snapshots"

    server_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("servers.id", ondelete="CASCADE"), index=True)
    run_id: Mapped[uuid.UUID] = mapped_column(index=True)
    phase: Mapped[str] = mapped_column(String(8), index=True)
    path: Mapped[str] = mapped_column(String(512), unique=True)
    raw_path: Mapped[str] = mapped_column(String(512))
    log_path: Mapped[str] = mapped_column(String(512))
    checksum: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    server: Mapped[Server] = relationship(back_populates="snapshots")
