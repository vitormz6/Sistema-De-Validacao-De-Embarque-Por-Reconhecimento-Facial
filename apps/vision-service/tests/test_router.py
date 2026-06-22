import cv2
from fastapi.testclient import TestClient

from app.api.router import get_vision_service
from app.main import app
from app.pipeline.service import VisionService
from tests.conftest import make_face, make_image
from tests.test_service import FakeFaceEngine


def _jpeg_bytes(image) -> bytes:
    ok, buffer = cv2.imencode(".jpg", image)
    assert ok
    return bytes(buffer)


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "vision-service"


def test_models_health_endpoint_reports_unloaded_by_default() -> None:
    client = TestClient(app)

    response = client.get("/health/models")

    assert response.status_code == 200
    assert response.json()["loaded"] is False


def test_generate_embedding_endpoint_happy_path() -> None:
    fake_engine = FakeFaceEngine(faces=[make_face()])
    app.dependency_overrides[get_vision_service] = lambda: VisionService(fake_engine)

    client = TestClient(app)
    image_bytes = _jpeg_bytes(make_image())

    try:
        response = client.post(
            "/embeddings/generate",
            files={"file": ("probe.jpg", image_bytes, "image/jpeg")},
        )
    finally:
        app.dependency_overrides.pop(get_vision_service, None)

    assert response.status_code == 200
    body = response.json()
    assert body["face_found"] is True
    assert len(body["embedding"]) == 512
    assert body["detector_name"] == "scrfd"


def test_generate_embedding_endpoint_no_face() -> None:
    fake_engine = FakeFaceEngine(faces=[])
    app.dependency_overrides[get_vision_service] = lambda: VisionService(fake_engine)

    client = TestClient(app)
    image_bytes = _jpeg_bytes(make_image())

    try:
        response = client.post(
            "/embeddings/generate",
            files={"file": ("probe.jpg", image_bytes, "image/jpeg")},
        )
    finally:
        app.dependency_overrides.pop(get_vision_service, None)

    assert response.status_code == 200
    body = response.json()
    assert body["face_found"] is False
    assert body["reason"] == "NO_FACE_DETECTED"
