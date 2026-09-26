import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Message(BaseModel):
    code: str
    message: str


class ServerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    address: str
    os_type: str
    enabled: bool
    wave: str | None
    created_at: datetime
    updated_at: datetime
    last_pre_check: datetime | None
    last_post_check: datetime | None
    last_connection_status: str | None
    current_status: str | None = None


class CredentialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    server_id: uuid.UUID
    kind: str
    username: str
    configured: bool = True


class GlobalCredentialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    os_type: str
    kind: str
    username: str
    configured: bool = True
