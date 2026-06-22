from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Boarding Face Validation - Central API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["local", "development", "staging", "production"] = "local"
    DEBUG: bool = True

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@postgres-central:5432/boarding_central"
    )

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    LOG_LEVEL: str = "INFO"

    # Auth / JWT
    JWT_SECRET_KEY: str = Field(default="change-me-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Edge devices (sync) authentication — shared key for MVP.
    # Future evolution: per-device credentials / mTLS.
    EDGE_SYNC_API_KEY: str = Field(default="change-me-edge-sync-key")

    # Vision Service integration
    VISION_SERVICE_URL: str = Field(default="http://vision-service:8002")
    VISION_SERVICE_TIMEOUT_SECONDS: float = 10.0

    # Biometrics / facial recognition
    EMBEDDING_DIMENSIONS: int = 512
    MIN_FACE_QUALITY_SCORE: float = 0.5
    MAX_SIMILARITY_DISTANCE: float = 0.4

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()