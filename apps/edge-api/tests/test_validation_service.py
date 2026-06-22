import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.connectivity import ConnectivityTracker
from app.modules.cache.model import LocalFaceEmbedding
from app.modules.cache.repository import PassengerCacheRepository, TicketCacheRepository
from app.modules.cache.vision_client import FaceEmbeddingResult
from app.modules.validation.service import (
    REASON_LOW_QUALITY,
    REASON_NO_ACTIVE_TICKET,
    REASON_NO_MATCH_WITHIN_THRESHOLD,
    REASON_PASSENGER_BLOCKED,
    REASON_SPOOF_SUSPECTED,
    BoardingValidationService,
)
from app.shared.enums import PassengerStatus, TicketStatus, ValidationStatus


def _vision_result(**overrides) -> FaceEmbeddingResult:
    payload = dict(
        face_found=True,
        embedding=[1.0, 0.0, 0.0],
        quality_score=0.9,
        model_name="arcface",
        model_version="buffalo_l",
        detector_name="scrfd",
        detector_version="buffalo_l",
        reason=None,
        liveness_score=0.95,
        spoof_suspected=False,
    )
    payload.update(overrides)
    return FaceEmbeddingResult(**payload)


def _service(
    session: AsyncSession,
    vision_result: FaceEmbeddingResult,
    *,
    candidates: list[LocalFaceEmbedding] | None = None,
    is_offline: bool = False,
) -> BoardingValidationService:
    service = BoardingValidationService(
        session,
        vision_client=AsyncMock(),
        connectivity_tracker=AsyncMock(spec=ConnectivityTracker),
    )
    service.vision_client.detect_and_embed = AsyncMock(return_value=vision_result)
    service.connectivity_tracker.is_offline = is_offline
    service.embedding_repository.list_active = AsyncMock(return_value=candidates or [])
    return service


async def _seed_passenger(
    session: AsyncSession, *, status: PassengerStatus = PassengerStatus.ACTIVE
) -> uuid.UUID:
    passenger_id = uuid.uuid4()
    await PassengerCacheRepository(session).upsert(
        id=passenger_id,
        full_name="Joao Silva",
        document_number="12345678900",
        status=status.value,
    )
    await session.commit()
    return passenger_id


async def _seed_active_ticket(session: AsyncSession, passenger_id: uuid.UUID) -> None:
    now = datetime.now(timezone.utc)
    await TicketCacheRepository(session).upsert(
        id=uuid.uuid4(),
        passenger_id=passenger_id,
        ticket_type="SINGLE",
        status=TicketStatus.ACTIVE.value,
        valid_from=now - timedelta(hours=1),
        valid_until=now + timedelta(hours=1),
    )
    await session.commit()


def _matching_embedding(passenger_id: uuid.UUID) -> LocalFaceEmbedding:
    return LocalFaceEmbedding(
        id=uuid.uuid4(),
        passenger_id=passenger_id,
        embedding=[1.0, 0.0, 0.0],
        model_name="arcface",
        model_version="buffalo_l",
    )


async def test_no_face_detected(db_session: AsyncSession) -> None:
    service = _service(db_session, _vision_result(face_found=False, embedding=None, reason="X"))

    result = await service.validate(b"img", "image/jpeg")

    assert result.status == ValidationStatus.DENIED_FACE_NOT_FOUND
    assert result.passenger_id is None


async def test_spoof_suspected(db_session: AsyncSession) -> None:
    service = _service(db_session, _vision_result(spoof_suspected=True))

    result = await service.validate(b"img", "image/jpeg")

    assert result.status == ValidationStatus.DENIED_SPOOF_SUSPECTED
    assert result.reason_code == REASON_SPOOF_SUSPECTED


async def test_low_quality(db_session: AsyncSession) -> None:
    service = _service(db_session, _vision_result(quality_score=0.1))

    result = await service.validate(b"img", "image/jpeg")

    assert result.status == ValidationStatus.DENIED_LOW_CONFIDENCE
    assert result.reason_code == REASON_LOW_QUALITY


async def test_no_match_within_threshold(db_session: AsyncSession) -> None:
    far_passenger_id = uuid.uuid4()
    candidates = [
        LocalFaceEmbedding(
            id=uuid.uuid4(),
            passenger_id=far_passenger_id,
            embedding=[0.0, 1.0, 0.0],
            model_name="arcface",
            model_version="buffalo_l",
        )
    ]
    service = _service(db_session, _vision_result(), candidates=candidates)

    result = await service.validate(b"img", "image/jpeg")

    assert result.status == ValidationStatus.DENIED_LOW_CONFIDENCE
    assert result.reason_code == REASON_NO_MATCH_WITHIN_THRESHOLD


async def test_passenger_blocked(db_session: AsyncSession) -> None:
    passenger_id = await _seed_passenger(db_session, status=PassengerStatus.BLOCKED)
    candidates = [_matching_embedding(passenger_id)]
    service = _service(db_session, _vision_result(), candidates=candidates)

    result = await service.validate(b"img", "image/jpeg")

    assert result.status == ValidationStatus.DENIED_PASSENGER_BLOCKED
    assert result.reason_code == REASON_PASSENGER_BLOCKED


async def test_no_active_ticket(db_session: AsyncSession) -> None:
    passenger_id = await _seed_passenger(db_session)
    candidates = [_matching_embedding(passenger_id)]
    service = _service(db_session, _vision_result(), candidates=candidates)

    result = await service.validate(b"img", "image/jpeg")

    assert result.status == ValidationStatus.DENIED_NO_ACTIVE_TICKET
    assert result.reason_code == REASON_NO_ACTIVE_TICKET


async def test_authorized_happy_path(db_session: AsyncSession) -> None:
    passenger_id = await _seed_passenger(db_session)
    await _seed_active_ticket(db_session, passenger_id)
    candidates = [_matching_embedding(passenger_id)]
    service = _service(db_session, _vision_result(), candidates=candidates, is_offline=True)

    result = await service.validate(b"img", "image/jpeg")

    assert result.status == ValidationStatus.AUTHORIZED
    assert result.passenger_id == passenger_id
    assert result.passenger_name == "Joao Silva"
    assert result.ticket_id is not None
    assert result.reason_code is None
    assert result.is_offline is True
    assert result.similarity_distance is not None and result.similarity_distance < 0.01


async def test_validation_is_persisted(db_session: AsyncSession) -> None:
    passenger_id = await _seed_passenger(db_session)
    await _seed_active_ticket(db_session, passenger_id)
    candidates = [_matching_embedding(passenger_id)]
    service = _service(db_session, _vision_result(), candidates=candidates)

    result = await service.validate(b"img", "image/jpeg")

    persisted = await service.log_repository.get_by_id(result.id)
    assert persisted is not None
    assert persisted.status == ValidationStatus.AUTHORIZED.value
    assert persisted.bus_id == settings.BUS_ID
    assert persisted.ticket_id == result.ticket_id
