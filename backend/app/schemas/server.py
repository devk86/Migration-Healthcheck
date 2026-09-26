import uuid

from pydantic import BaseModel, Field


class ServerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=255)
    os_type: str
    enabled: bool = True
    wave: str | None = None


class ServerUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    os_type: str | None = None
    enabled: bool | None = None
    wave: str | None = None


class CredentialCreate(BaseModel):
    kind: str
    username: str = Field(min_length=1, max_length=255)
    secret: str = Field(min_length=1, max_length=100000)


class ImportResult(BaseModel):
    mode: str
    imported: int
    rows: list[dict[str, object]]
    errors: list[dict[str, object]]


class ConnectionTestRead(BaseModel):
    ok: bool
    code: str
    message: str
    server_id: uuid.UUID
