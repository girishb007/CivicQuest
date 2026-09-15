from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CQ_", env_file=".env", extra="ignore")
    env: str = "local"
    demo_mode: bool = True
    database_url: str = "postgresql+psycopg://civicquest:civicquest@localhost:55432/civicquest"
    redis_url: str = "redis://localhost:56379/0"
    origin: str = "http://localhost:3000"
    secret: str = "local-only-change-this-secret-before-sharing"
    storage: str = "filesystem"
    media_root: Path = Path(".local/media")
    queue_mode: str = "sqs"
    queue_url: str = "http://localhost:9324/000000000000/civicquest"
    sqs_endpoint: str | None = "http://localhost:9324"
    aws_region: str = "ap-south-1"
    original_bucket: str = ""
    derivative_bucket: str = ""
    google_client_id: str = ""
    google_client_secret: str = ""
    bedrock_model_id: str = ""
    maptiler_key: str = ""
    catches_public: bool = False
    public_data_approved: bool = False
    vapid_private_key: str = ""
    vapid_public_key: str = ""
    vapid_subject: str = "mailto:operator@example.invalid"
    max_upload_bytes: int = 50 * 1024 * 1024
    max_image_pixels: int = 40_000_000
    report_daily_xp_cap: int = 100
    original_retention_days: int = 30
    audit_retention_days: int = 365
    security_retention_days: int = 14

    @model_validator(mode="after")
    def production_guards(self):
        if self.env not in {"local", "test"}:
            if self.demo_mode or self.secret.startswith("local-") or len(self.secret) < 32:
                raise ValueError("Live environments require demo mode off and a strong secret")
            if not self.origin.startswith("https://") or self.storage != "s3":
                raise ValueError("Live environments require HTTPS and S3")
            if not self.public_data_approved:
                raise ValueError("Approve the geographic dataset before live use")
        return self


@lru_cache
def settings() -> Settings:
    return Settings()
