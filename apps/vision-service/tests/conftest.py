import cv2
import numpy as np
import pytest

from app.pipeline.face_engine import DetectedFace


def make_image(
    width: int = 400,
    height: int = 400,
    noise: bool = False,
) -> np.ndarray:
    """A plain BGR numpy image, optionally with random per-pixel noise."""
    if noise:
        rng = np.random.default_rng(seed=42)
        return rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)

    image = np.full((height, width, 3), 130, dtype=np.uint8)
    return image


def make_periodic_image(width: int = 400, height: int = 400, period: int = 4) -> np.ndarray:
    """
    A synthetic checkerboard-like pattern: strong, regular high-frequency
    content, similar in spirit to moire artifacts from a screen/print
    recapture — used to exercise the liveness "spoof_suspected" branch.
    """
    y, x = np.mgrid[0:height, 0:width]
    pattern = (((x // period) + (y // period)) % 2) * 255
    gray = pattern.astype(np.uint8)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def make_face(
    bbox: tuple[float, float, float, float] = (100, 100, 300, 300),
    detection_score: float = 0.95,
    embedding: list[float] | None = None,
    keypoints: np.ndarray | None = None,
) -> DetectedFace:
    # Default to a plausible 512-d embedding unless the caller explicitly
    # wants to test the "no embedding" case via DetectedFace directly.
    if embedding is None:
        embedding = [0.1] * 512

    if keypoints is None:
        # Roughly frontal 5-point layout: left_eye, right_eye, nose,
        # left_mouth, right_mouth, scaled to sit inside the default bbox.
        keypoints = np.array(
            [
                [150, 160],
                [250, 160],
                [200, 200],
                [160, 250],
                [240, 250],
            ],
            dtype=np.float32,
        )

    return DetectedFace(
        bbox=np.array(bbox, dtype=np.float32),
        keypoints=keypoints,
        detection_score=detection_score,
        embedding=None if embedding is None else np.array(embedding, dtype=np.float32),
    )


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
