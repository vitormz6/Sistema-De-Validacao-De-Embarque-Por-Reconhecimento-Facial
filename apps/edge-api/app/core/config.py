from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Boarding Face Validation - Edge API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["local", "development", "staging", "production"] = "local"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Identifies this vehicle to the central API during sync.
    BUS_ID: str = Field(default="bus-01")

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@postgres-edge:5432/boarding_edge"
    )

    VISION_SERVICE_URL: str = Field(default="http://vision-service:8002")
    VISION_SERVICE_TIMEOUT_SECONDS: float = 10.0

    MIN_FACE_QUALITY_SCORE: float = 0.5
    MAX_SIMILARITY_DISTANCE: float = 0.4

    CENTRAL_API_URL: str = Field(default="http://central-api:8000")
    CENTRAL_API_PING_TIMEOUT_SECONDS: float = 2.0

    # Browsers that are allowed to call the edge-api directly.
    # The operator-web runs on port 5174; add the device's LAN IP here in
    # production (e.g. "http://192.168.1.10:5174").
    CORS_ORIGINS: list[str] = [
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
