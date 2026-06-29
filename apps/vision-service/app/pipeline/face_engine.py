# Wrapper do insightface. Carrega só detecção (SCRFD) e reconhecimento (ArcFace),
# os outros módulos do buffalo_l (idade, gênero) não são necessários.

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
    """Inicializa o modelo insightface de forma lazy (só carrega quando precisar)."""

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
        """Recebe imagem BGR (OpenCV) e retorna as faces detectadas."""
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
