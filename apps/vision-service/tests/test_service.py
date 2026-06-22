import cv2
import numpy as np

from app.pipeline.face_engine import DetectedFace
from app.pipeline.service import (
    REASON_EMBEDDING_UNAVAILABLE,
    REASON_INVALID_IMAGE,
    REASON_MULTIPLE_FACES_DETECTED,
    REASON_NO_FACE_DETECTED,
    VisionService,
)
from tests.conftest import make_face, make_image


class FakeFaceEngine:
    """Stands in for the real insightface-backed FaceEngine in tests."""

    def __init__(self, faces=None) -> None:
        self._faces = faces or []
        self.received_images = []

    def detect_faces(self, image):
        self.received_images.append(image)
        return self._faces


def _jpeg_bytes(image) -> bytes:
    ok, buffer = cv2.imencode(".jpg", image)
    assert ok
    return bytes(buffer)


def test_invalid_image_bytes_returns_invalid_image_reason() -> None:
    service = VisionService(FakeFaceEngine())

    result = service.generate_embedding(b"this is not an image")

    assert result.face_found is False
    assert result.reason == REASON_INVALID_IMAGE


def test_no_face_detected() -> None:
    service = VisionService(FakeFaceEngine(faces=[]))
    image_bytes = _jpeg_bytes(make_image())

    result = service.generate_embedding(image_bytes)

    assert result.face_found is False
    assert result.reason == REASON_NO_FACE_DETECTED


def test_embedding_unavailable_when_recognition_did_not_run() -> None:
    # Built directly (not via make_face) so `embedding` stays None — this
    # is what a detection-only result looks like if the recognition model
    # somehow didn't run on a detected face.
    face_without_embedding = DetectedFace(
        bbox=np.array([100, 100, 300, 300], dtype=np.float32),
        keypoints=None,
        detection_score=0.9,
        embedding=None,
    )
    service = VisionService(FakeFaceEngine(faces=[face_without_embedding]))
    image_bytes = _jpeg_bytes(make_image())

    result = service.generate_embedding(image_bytes)

    assert result.face_found is False
    assert result.reason == REASON_EMBEDDING_UNAVAILABLE


def test_happy_path_returns_full_result() -> None:
    face = make_face(detection_score=0.93)
    service = VisionService(FakeFaceEngine(faces=[face]))
    image_bytes = _jpeg_bytes(make_image())

    result = service.generate_embedding(image_bytes)

    assert result.face_found is True
    assert result.embedding is not None
    assert len(result.embedding) == 512
    assert result.model_name == "arcface"
    assert result.detector_name == "scrfd"
    assert result.liveness_score is not None
    assert result.spoof_suspected is not None
    assert result.reason is None


def test_multiple_faces_picks_highest_score_and_flags_reason() -> None:
    weak_face = make_face(bbox=(10, 10, 50, 50), detection_score=0.55)
    strong_face = make_face(bbox=(100, 100, 300, 300), detection_score=0.98)
    service = VisionService(FakeFaceEngine(faces=[weak_face, strong_face]))
    image_bytes = _jpeg_bytes(make_image())

    result = service.generate_embedding(image_bytes)

    assert result.face_found is True
    assert result.reason == REASON_MULTIPLE_FACES_DETECTED
