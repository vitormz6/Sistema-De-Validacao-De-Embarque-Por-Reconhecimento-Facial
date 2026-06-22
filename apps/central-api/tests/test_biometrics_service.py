import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import NotFoundError, ValidationFailedError
from app.modules.biometrics.model import FaceEmbedding
from app.modules.biometrics.service import BiometricService
from app.modules.biometrics.vision_client import FaceEmbeddingResult
from app.shared.enums import ValidationStatus


def _make_service(vision_result: FaceEmbeddingResult, passenger=object()):
    """
    Biometrics depends on pgvector (no SQLite equivalent), so these tests
    mock the repository and vision_client instead of using `db_session`,
    focusing on the business rules: quality gate, versioning and the
    compare decision threshold.
    """
    service = BiometricService(session=AsyncMock(), vision_client=AsyncMock())
    service.vision_client.detect_and_embed = AsyncMock(return_value=vision_result)
    service.repository = AsyncMock()
    service.passenger_repository = AsyncMock()
    service.passenger_repository.get_by_id = AsyncMock(return_value=passenger)
    return service


def _embedding_result(**overrides) -> FaceEmbeddingResult:
    payload = dict(
        face_found=True,
        embedding=[0.1] * 512,
        quality_score=0.9,
        model_name="arcface",
        model_version="buffalo_l_v1",
        detector_name="scrfd",
        detector_version="v1",
        reason=None,
    )
    payload.update(overrides)
    return FaceEmbeddingResult(**payload)


async def test_enroll_rejects_unknown_passenger() -> None:
    service = _make_service(_embedding_result(), passenger=None)

    with pytest.raises(NotFoundError):
        await service.enroll(uuid.uuid4(), b"fake-image", "image/jpeg")


async def test_enroll_rejects_when_no_face_found() -> None:
    service = _make_service(_embedding_result(face_found=False, embedding=None))

    with pytest.raises(ValidationFailedError):
        await service.enroll(uuid.uuid4(), b"fake-image", "image/jpeg")


async def test_enroll_rejects_low_quality_image() -> None:
    service = _make_service(_embedding_result(quality_score=0.1))

    with pytest.raises(ValidationFailedError):
        await service.enroll(uuid.uuid4(), b"fake-image", "image/jpeg")


async def test_enroll_revokes_previous_embedding_before_creating_new(monkeypatch) -> None:
    service = _make_service(_embedding_result())
    created = FaceEmbedding(passenger_id=uuid.uuid4(), embedding=[0.1] * 512)
    service.repository.create = AsyncMock(return_value=created)
    service.repository.revoke_active = AsyncMock()

    await service.enroll(uuid.uuid4(), b"fake-image", "image/jpeg")

    service.repository.revoke_active.assert_awaited_once()
    service.repository.create.assert_awaited_once()


async def test_enroll_rejects_suspected_spoof() -> None:
    service = _make_service(_embedding_result(spoof_suspected=True))

    with pytest.raises(ValidationFailedError):
        await service.enroll(uuid.uuid4(), b"fake-image", "image/jpeg")


async def test_compare_denies_suspected_spoof_without_searching() -> None:
    service = _make_service(_embedding_result(spoof_suspected=True))
    service.repository.find_nearest = AsyncMock()

    result = await service.compare(b"fake-image", "image/jpeg")

    assert result.decision == ValidationStatus.DENIED_SPOOF_SUSPECTED.value
    assert result.matched_passenger_id is None
    service.repository.find_nearest.assert_not_awaited()


async def test_compare_returns_face_not_found_when_no_face_in_probe() -> None:
    service = _make_service(_embedding_result(face_found=False, embedding=None))

    result = await service.compare(b"fake-image", "image/jpeg")

    assert result.decision == ValidationStatus.DENIED_FACE_NOT_FOUND.value
    assert result.matched_passenger_id is None


async def test_compare_authorizes_within_threshold() -> None:
    passenger_id = uuid.uuid4()
    matched_embedding = FaceEmbedding(passenger_id=passenger_id, embedding=[0.1] * 512)

    service = _make_service(_embedding_result())
    service.repository.find_nearest = AsyncMock(return_value=[(matched_embedding, 0.1)])

    result = await service.compare(b"fake-image", "image/jpeg")

    assert result.decision == ValidationStatus.AUTHORIZED.value
    assert result.matched_passenger_id == passenger_id
    assert result.distance == 0.1


async def test_compare_denies_low_confidence_outside_threshold() -> None:
    passenger_id = uuid.uuid4()
    far_embedding = FaceEmbedding(passenger_id=passenger_id, embedding=[0.1] * 512)

    service = _make_service(_embedding_result())
    service.repository.find_nearest = AsyncMock(return_value=[(far_embedding, 0.9)])

    result = await service.compare(b"fake-image", "image/jpeg")

    assert result.decision == ValidationStatus.DENIED_LOW_CONFIDENCE.value
    assert result.matched_passenger_id is None
