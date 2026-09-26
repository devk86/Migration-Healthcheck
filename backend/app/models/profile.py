from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKey


class CheckProfile(UUIDPrimaryKey, Base):
    __tablename__ = "check_profiles"

    name: Mapped[str] = mapped_column(String(128), unique=True)
    checks: Mapped[list[str]] = mapped_column(JSON)
