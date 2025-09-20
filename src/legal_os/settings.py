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
    enable_gptqa: bool = False
    enable_aad: bool = False
    enable_keyvault: bool = False
    enable_external_ai: bool = False


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

    # Optional AI provider configuration (stubbed in dev)
    ai_provider: str | None = None  # e.g., "azure", "openai"
    ai_endpoint: str | None = None
    ai_api_key: str | None = None
    qa_model_primary: str = "gpt-5"
    qa_model_fallback: str = "gpt-5-mini"

    # Azure AD (optional)
    aad_tenant_id: str | None = None
    aad_client_id: str | None = None
    aad_audience: str | None = None

    # Azure Key Vault (optional)
    keyvault_uri: str | None = None

    # Optional feature flags (can be set via env nesting FLAGS__*)
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
        - when external AI is enabled, require configured provider and endpoint
        - when GPT QA is enabled, ensure models configured
        - when AAD is enabled, require tenant/client/audience
        - when Key Vault is enabled, require keyvault_uri
        """
        if not self.app_name:
            raise ValueError("APP_NAME must be set")

        if self.env == "production":
            if self.debug:
                raise ValueError("DEBUG must be False in production")
            if self.is_sqlite:
                raise ValueError("SQLite is not allowed in production")
            if not self.jwt_secret and not self.flags.enable_aad:
                raise ValueError("JWT_SECRET must be set in production (or enable AAD)")

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

        if self.flags.enable_external_ai:
            if not self.ai_provider or not self.ai_endpoint:
                raise ValueError("External AI enabled but AI_PROVIDER/AI_ENDPOINT not set")

        if self.flags.enable_gptqa:
            if not self.qa_model_primary or not self.qa_model_fallback:
                raise ValueError("GPT QA enabled but models not configured")

        if self.flags.enable_aad:
            if not self.aad_tenant_id or not self.aad_client_id or not self.aad_audience:
                raise ValueError("AAD enabled but tenant/client/audience not configured")

        if self.flags.enable_keyvault and not self.keyvault_uri:
            raise ValueError("Key Vault enabled but KEYVAULT_URI is missing")


@lru_cache
def get_settings() -> Settings:
    return Settings()
