import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthCheckCreate(BaseModel):
    server_ids: list[uuid.UUID] = Field(min_length=1)
    phase: str


class HealthCheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phase: str
    status: str
    server_ids: list[str]
    total: int
    completed: int
    running_count: int
    failed_count: int
    queued_count: int
    cancel_requested: bool
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class HealthCheckResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    run_id: uuid.UUID
    server_id: uuid.UUID
    status: str
    error_code: str | None
    message: str | None
    snapshot_id: uuid.UUID | None


class SnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    server_id: uuid.UUID
    run_id: uuid.UUID
    phase: str
    checksum: str
    created_at: datetime
