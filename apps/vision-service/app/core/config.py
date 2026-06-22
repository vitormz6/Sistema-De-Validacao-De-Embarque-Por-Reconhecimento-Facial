from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Boarding Face Validation - Vision Service"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["local", "development", "staging", "production"] = "local"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # insightface model pack: bundles the SCRFD detector + ArcFace
    # recognizer as a single download (see app/pipeline/face_engine.py).
    MODEL_PACK_NAME: str = "buffalo_l"
    MODEL_ROOT: str = Field(default="/app/.insightface")

    # -1 = CPU. Set to a GPU device id only if onnxruntime-gpu is installed
    # instead of the CPU build declared in pyproject.toml.
    CTX_ID: int = -1

    DET_SIZE_WIDTH: int = 640
    DET_SIZE_HEIGHT: int = 640
    DET_THRESH: float = 0.5

    # Quality scoring (app/pipeline/quality.py)
    MIN_FACE_SIZE_RATIO: float = 0.05
    BLUR_VARIANCE_REFERENCE: float = 120.0
    BRIGHTNESS_MIN: float = 40.0
    BRIGHTNESS_MAX: float = 215.0

    # Basic liveness heuristic (app/pipeline/liveness.py) — see RFC 3.4
    # (R2/M6): heuristic-only for the MVP, not a trained anti-spoofing model.
    LIVENESS_MIN_SHARPNESS_VARIANCE: float = 15.0
    LIVENESS_FREQ_PEAK_RATIO_THRESHOLD: float = 0.05

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def det_size(self) -> tuple[int, int]:
        return (self.DET_SIZE_WIDTH, self.DET_SIZE_HEIGHT)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
