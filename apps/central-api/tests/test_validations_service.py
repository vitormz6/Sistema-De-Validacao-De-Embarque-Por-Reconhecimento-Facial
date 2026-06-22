from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.validations.schema import ValidationEventIngest
from app.modules.validations.service import ValidationService
from app.shared.enums import ValidationStatus


def _event(external_id: str, **overrides) -> ValidationEventIngest:
    payload = {
        "external_id": external_id,
        "bus_id": "bus-01",
        "status": ValidationStatus.AUTHORIZED,
        "captured_at": datetime.now(timezone.utc),
    }
    payload.update(overrides)
    return ValidationEventIngest(**payload)


async def test_register_events_creates_new_records(db_session: AsyncSession) -> None:
    service = ValidationService(db_session)

    result = await service.register_events([_event("evt-1"), _event("evt-2")])

    assert sorted(result.accepted) == ["evt-1", "evt-2"]
    assert result.duplicated == []
    assert result.rejected == []


async def test_register_events_is_idempotent(db_session: AsyncSession) -> None:
    """
    RF11: retried syncs from the edge must not create duplicate boarding
    validations. Pushing the same external_id twice should land in
    `duplicated` the second time.
    """
    service = ValidationService(db_session)

    await service.register_events([_event("evt-retry")])
    second_result = await service.register_events([_event("evt-retry")])

    assert second_result.accepted == []
    assert second_result.duplicated == ["evt-retry"]

    listed, total = await service.list_validations(
        page=1,
        page_size=20,
        status=None,
        passenger_id=None,
        bus_id=None,
        captured_from=None,
        captured_to=None,
    )

    assert total == 1
    assert len(listed) == 1


async def test_register_events_dedupes_within_the_same_batch(db_session: AsyncSession) -> None:
    """
    Each item is flushed before the next is checked, so a repeated
    external_id inside a single push (not just across retried pushes) is
    also caught.
    """
    service = ValidationService(db_session)

    result = await service.register_events(
        [_event("evt-a"), _event("evt-a"), _event("evt-b")]
    )

    assert sorted(result.accepted) == ["evt-a", "evt-b"]
    assert result.duplicated == ["evt-a"]
    assert result.rejected == []


async def test_get_stats_counts_grouped_by_status(db_session: AsyncSession) -> None:
    service = ValidationService(db_session)

    await service.register_events(
        [
            _event("evt-stats-1", status=ValidationStatus.AUTHORIZED),
            _event("evt-stats-2", status=ValidationStatus.AUTHORIZED),
            _event("evt-stats-3", status=ValidationStatus.DENIED_LOW_CONFIDENCE),
        ]
    )

    stats = await service.get_stats()

    assert stats.by_status["AUTHORIZED"] == 2
    assert stats.by_status["DENIED_LOW_CONFIDENCE"] == 1
    assert stats.total == 3


async def test_get_stats_with_no_validations_returns_empty(db_session: AsyncSession) -> None:
    service = ValidationService(db_session)

    stats = await service.get_stats()

    assert stats.by_status == {}
    assert stats.total == 0
