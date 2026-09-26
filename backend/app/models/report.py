import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKey, utcnow


class Report(UUIDPrimaryKey, Base):
    __tablename__ = "reports"

    comparison_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("comparisons.id", ondelete="CASCADE"),
        index=True,
    )
    format: Mapped[str] = mapped_column(String(8))
    path: Mapped[str] = mapped_column(String(512))
    created_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    comparison: Mapped[Comparison] = relationship(back_populates="reports")
