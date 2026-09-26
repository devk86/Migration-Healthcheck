from sqlalchemy import select

from app.config import get_settings
from app.database.database import get_sessionmaker
from app.models import CheckProfile, User
from app.security.passwords import hash_password

DEFAULT_CHECKS = ["os", "cpu", "memory", "disk", "network", "services", "processes", "software"]


def ensure_admin() -> None:
    settings = get_settings()
    session = get_sessionmaker()()
    try:
        existing = session.scalar(select(User).where(User.username == settings.admin_username))
        if existing is None:
            session.add(
                User(
                    username=settings.admin_username,
                    password_hash=hash_password(settings.admin_password),
                    role="admin",
                )
            )
        profile = session.scalar(select(CheckProfile).where(CheckProfile.name == "Default Server"))
        if profile is None:
            session.add(CheckProfile(name="Default Server", checks=DEFAULT_CHECKS))
        session.commit()
    finally:
        session.close()


def main() -> None:
    ensure_admin()
    if get_settings().seed_on_startup:
        from app.utils.seed import seed_if_empty

        seed_if_empty()


if __name__ == "__main__":
    main()
