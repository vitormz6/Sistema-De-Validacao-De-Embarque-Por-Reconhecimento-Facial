from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.modules.validation.router import get_validation_service
from app.modules.validation.schema import BoardingValidationResponse
from app.shared.enums import ValidationStatus


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "edge-api"


def test_validate_boarding_endpoint_uses_overridden_service() -> None:
    fake_response = BoardingValidationResponse(
        id="11111111-1111-1111-1111-111111111111",
        status=ValidationStatus.AUTHORIZED,
        passenger_id=None,
        passenger_name=None,
        ticket_id=None,
        confidence_score=0.98,
        similarity_distance=0.02,
        reason_code=None,
        is_offline=False,
        captured_at=datetime.now(timezone.utc),
    )

    fake_service = AsyncMock()
    fake_service.validate = AsyncMock(return_value=fake_response)
    app.dependency_overrides[get_validation_service] = lambda: fake_service

    client = TestClient(app)

    try:
        response = client.post(
            "/local/validate-boarding",
            files={"file": ("probe.jpg", b"fake-bytes", "image/jpeg")},
        )
    finally:
        app.dependency_overrides.pop(get_validation_service, None)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "AUTHORIZED"
    fake_service.validate.assert_awaited_once()
