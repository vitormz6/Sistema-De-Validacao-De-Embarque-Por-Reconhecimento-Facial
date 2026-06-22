from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Boarding Face Validation - Sync Worker"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["local", "development", "staging", "production"] = "local"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    BUS_ID: str = Field(default="bus-01")

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@postgres-edge:5432/boarding_edge"
    )

    CENTRAL_API_URL: str = Field(default="http://central-api:8000")
    CENTRAL_API_TIMEOUT_SECONDS: float = 10.0
    EDGE_SYNC_API_KEY: str = Field(default="change-me-edge-sync-key")

    SYNC_INTERVAL_SECONDS: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
