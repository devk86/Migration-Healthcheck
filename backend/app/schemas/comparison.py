import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ComparisonCreate(BaseModel):
    pre_snapshot_id: uuid.UUID
    post_snapshot_id: uuid.UUID


class ComparisonResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    metric: str
    pre_value: str
    post_value: str
    change: str
    status: str
    changed: bool


class ComparisonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    server_id: uuid.UUID
    pre_snapshot_id: uuid.UUID
    post_snapshot_id: uuid.UUID
    overall_status: str
    created_at: datetime
    results: list[ComparisonResultRead] = []


class ReportCreate(BaseModel):
    comparison_id: uuid.UUID
    format: str


class ReportChoiceRead(BaseModel):
    server_id: uuid.UUID
    server_name: str
    kind: str
    snapshot_id: uuid.UUID | None = None
    comparison_id: uuid.UUID | None = None


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    comparison_id: uuid.UUID
    format: str
    created_at: datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
