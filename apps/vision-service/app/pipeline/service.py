"""
Orchestrates the full per-request pipeline: decode -> detect -> pick best
face -> quality -> liveness -> embedding. This is the only place that knows
about the response contract central-api's `vision_client.py` expects.
"""

from dataclasses import dataclass

import cv2
import numpy as np

from app.core.config import settings
from app.pipeline.face_engine import DetectedFace, FaceEngine
from app.pipeline.liveness import assess_liveness
from app.pipeline.quality import compute_quality_score, crop_face

REASON_INVALID_IMAGE = "INVALID_IMAGE"
REASON_NO_FACE_DETECTED = "NO_FACE_DETECTED"
REASON_EMBEDDING_UNAVAILABLE = "EMBEDDING_UNAVAILABLE"
REASON_MULTIPLE_FACES_DETECTED = "MULTIPLE_FACES_DETECTED"

DETECTOR_NAME = "scrfd"
MODEL_NAME = "arcface"


@dataclass(frozen=True, slots=True)
class EmbeddingResult:
    face_found: bool
    embedding: list[float] | None = None
    quality_score: float | None = None
    liveness_score: float | None = None
    spoof_suspected: bool | None = None
    model_name: str | None = None
    model_version: str | None = None
    detector_name: str | None = None
    detector_version: str | None = None
    reason: str | None = None


def _decode_image(image_bytes: bytes) -> np.ndarray | None:
    buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    return image


def _pick_best_face(faces: list[DetectedFace]) -> DetectedFace:
    return max(faces, key=lambda face: face.detection_score)


class VisionService:
    def __init__(self, face_engine: FaceEngine) -> None:
        self.face_engine = face_engine

    def generate_embedding(self, image_bytes: bytes) -> EmbeddingResult:
        image = _decode_image(image_bytes)

        if image is None or image.size == 0:
            return EmbeddingResult(face_found=False, reason=REASON_INVALID_IMAGE)

        faces = self.face_engine.detect_faces(image)

        if not faces:
            return EmbeddingResult(face_found=False, reason=REASON_NO_FACE_DETECTED)

        best_face = _pick_best_face(faces)

        if best_face.embedding is None:
            return EmbeddingResult(face_found=False, reason=REASON_EMBEDDING_UNAVAILABLE)

        quality_score = compute_quality_score(image, best_face)

        face_crop = crop_face(image, best_face.bbox)
        liveness = assess_liveness(face_crop)

        return EmbeddingResult(
            face_found=True,
            embedding=[float(x) for x in best_face.embedding],
            quality_score=quality_score,
            liveness_score=liveness.liveness_score,
            spoof_suspected=liveness.spoof_suspected,
            model_name=MODEL_NAME,
            model_version=settings.MODEL_PACK_NAME,
            detector_name=DETECTOR_NAME,
            detector_version=settings.MODEL_PACK_NAME,
            reason=REASON_MULTIPLE_FACES_DETECTED if len(faces) > 1 else None,
        )
