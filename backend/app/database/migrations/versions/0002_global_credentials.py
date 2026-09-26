"""Global Linux and Windows credentials."""

from alembic import op
from app.models import Base

revision = "0002_global_credentials"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    op.drop_table("global_credentials")
