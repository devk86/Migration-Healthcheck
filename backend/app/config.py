from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_version: str = "1.0.0"
    database_url: str = (
        "postgresql+psycopg://healthcheck:healthcheck@localhost:5432/healthcheck"
    )
    redis_url: str = "redis://localhost:6379/0"
    data_dir: str = "./data"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"
    mock_connectors: bool = False
    credential_key: str = ""
    jwt_secret: str = "dev-only-change-me"
    jwt_ttl_minutes: int = 720
    admin_username: str = "admin"
    admin_password: str = "admin"
    seed_on_startup: bool = False
    celery_eager: bool = False
    ssh_port: int = 22
    ssh_connect_timeout: int = 10
    ssh_command_timeout: int = 60
    winrm_port: int = 5985
    winrm_transport: str = "ntlm"
    winrm_server_cert_validation: str = "ignore"
    winrm_timeout: int = 30
    celery_worker_concurrency: int = 10
    max_upload_bytes: int = 1_048_576
    rate_limit_per_minute: int = 120
    storage_backend: str = "local"
    credential_backend: str = "local"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def psycopg_url(self) -> str:
        return self.database_url.replace("postgresql+psycopg://", "postgresql://", 1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
