"""ORM models. Importing this package registers every table on Base.metadata."""

from app.models.audit import AuditLog
from app.models.base import Base
from app.models.comparison import Comparison, ComparisonResult
from app.models.healthcheck_run import HealthCheckResult, HealthCheckRun
from app.models.profile import CheckProfile
from app.models.report import Report
from app.models.server import Credential, GlobalCredential, Server
from app.models.snapshot import Snapshot
from app.models.user import User

__all__ = [
    "AuditLog",
    "Base",
    "CheckProfile",
    "Comparison",
    "ComparisonResult",
    "Credential",
    "GlobalCredential",
    "HealthCheckResult",
    "HealthCheckRun",
    "Report",
    "Server",
    "Snapshot",
    "User",
]
