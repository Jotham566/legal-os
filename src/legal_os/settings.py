from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "development"
    debug: bool = True
    app_name: str = "legal-os"
    # Default to file-based SQLite for dev; tests can override to in-memory
    database_url: str = "sqlite+pysqlite:///./legal_os.db"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
