"""
Thin wrapper around insightface's `FaceAnalysis`.

We only load the "detection" (SCRFD) and "recognition" (ArcFace) sub-models
from the buffalo_l pack — it also ships age/gender/landmark models we don't
need for boarding validation, so skipping them keeps memory and startup
time down.

Model weights are downloaded automatically by insightface on first use
(into `settings.MODEL_ROOT`) and require outbound internet access on first
boot; afterwards they're read from the local cache/volume (see
docker-compose.yml's `insightface-models` volume).
"""

from dataclasses import dataclass
from threading import Lock
from typing import Any

import numpy as np

from app.core.config import settings

ALLOWED_MODULES = ("detection", "recognition")


@dataclass(frozen=True, slots=True)
class DetectedFace:
    bbox: np.ndarray  # [x1, y1, x2, y2]
    keypoints: np.ndarray | None  # 5x2 landmarks (eyes, nose, mouth corners)
    detection_score: float
    embedding: np.ndarray | None  # 512-d, set once the recognition model ran


class FaceEngine:
    """
    Lazily initializes the underlying insightface `FaceAnalysis` instance.

    Lazy on purpose: importing/constructing the engine must not trigger a
    model download or ONNX session creation at module import time (would
    slow down app startup and break tests that never need real inference)
    — it only happens on the first real call to `detect_faces`.
    """

    def __init__(self) -> None:
        self._app: Any | None = None
        self._lock = Lock()

    def _ensure_loaded(self) -> Any:
        if self._app is not None:
            return self._app

        with self._lock:
            if self._app is not None:
                return self._app

            from insightface.app import FaceAnalysis

            face_app = FaceAnalysis(
                name=settings.MODEL_PACK_NAME,
                root=settings.MODEL_ROOT,
                allowed_modules=list(ALLOWED_MODULES),
            )
            face_app.prepare(
                ctx_id=settings.CTX_ID,
                det_thresh=settings.DET_THRESH,
                det_size=settings.det_size,
            )
            self._app = face_app
            return face_app

    def is_loaded(self) -> bool:
        return self._app is not None

    def detect_faces(self, image: np.ndarray) -> list[DetectedFace]:
        """
        `image` must be a BGR numpy array (as returned by `cv2.imdecode`),
        the format both OpenCV and insightface expect.
        """
        face_app = self._ensure_loaded()
        raw_faces = face_app.get(image)

        return [
            DetectedFace(
                bbox=np.asarray(face.bbox),
                keypoints=None if face.kps is None else np.asarray(face.kps),
                detection_score=float(face.det_score),
                embedding=None if face.embedding is None else np.asarray(face.embedding),
            )
            for face in raw_faces
        ]


_engine: FaceEngine | None = None


def get_face_engine() -> FaceEngine:
    global _engine
    if _engine is None:
        _engine = FaceEngine()
    return _engine
