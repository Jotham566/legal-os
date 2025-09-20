from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class FeatureFlags(BaseModel):
    enable_minio: bool = False
    enable_redis: bool = False
    enable_elasticsearch: bool = False
    enable_pgvector: bool = False


class Settings(BaseSettings):
    env: Literal["development", "test", "production"] = "development"
    debug: bool = True
    app_name: str = "legal-os"
    # Default to file-based SQLite for dev; tests can override to in-memory
    database_url: str = "sqlite+pysqlite:///./legal_os.db"
    # Auth/JWT
    jwt_secret: str | None = None
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_expire_minutes: int = 60
    # Uploads
    max_upload_mb: int = 500
    uploads_dir: str = "./uploads"

    # Optional MinIO (S3-compatible) for document storage
    minio_endpoint: str | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None
    minio_bucket: str | None = None
    minio_secure: bool = True

    # Optional feature flags (can be set via env nesting FLAGS__ENABLE_MINIO=true, etc.)
    flags: FeatureFlags = FeatureFlags()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    # Convenience properties
    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite+")

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql+") or self.database_url.startswith(
            "postgresql://"
        )

    def assert_valid(self) -> None:
        """Validate configuration invariants, raising ValueError for illegal combinations.

        - production must not use sqlite
        - production must have debug == False
        - app_name must be non-empty
        - if enable_pgvector, require a Postgres URL
        """
        if not self.app_name:
            raise ValueError("APP_NAME must be set")

        if self.env == "production":
            if self.debug:
                raise ValueError("DEBUG must be False in production")
            if self.is_sqlite:
                raise ValueError("SQLite is not allowed in production")
            if not self.jwt_secret:
                raise ValueError("JWT_SECRET must be set in production")

        if self.flags.enable_pgvector and not self.is_postgres:
            raise ValueError("pgvector requires a PostgreSQL DATABASE_URL")

        if self.flags.enable_minio:
            missing = [
                k
                for k, v in {
                    "MINIO_ENDPOINT": self.minio_endpoint,
                    "MINIO_ACCESS_KEY": self.minio_access_key,
                    "MINIO_SECRET_KEY": self.minio_secret_key,
                    "MINIO_BUCKET": self.minio_bucket,
                }.items()
                if not v
            ]
            if missing:
                raise ValueError(
                    "MinIO is enabled but missing required settings: " + ", ".join(missing)
                )


@lru_cache
def get_settings() -> Settings:
    return Settings()
