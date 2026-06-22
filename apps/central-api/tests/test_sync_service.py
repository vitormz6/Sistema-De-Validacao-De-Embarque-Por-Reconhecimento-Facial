import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.passengers.schema import PassengerCreate
from app.modules.passengers.service import PassengerService
from app.modules.sync.service import SyncService
from app.modules.tickets.schema import TicketCreate
from app.modules.tickets.service import TicketService
from app.modules.validations.schema import ValidationEventIngest
from app.shared.enums import ValidationStatus


async def _build_sync_service(session: AsyncSession) -> SyncService:
    service = SyncService(session)
    # face_embeddings has no SQLite-compatible column type in this test DB
    # (see conftest.py); biometrics pull is exercised separately via mocks.
    service.embedding_repository.list_active = AsyncMock(return_value=[])
    return service


async def test_pull_returns_only_active_passengers_and_tickets(db_session: AsyncSession) -> None:
    passenger_service = PassengerService(db_session)
    ticket_service = TicketService(db_session)

    active_passenger = await passenger_service.create_passenger(
        PassengerCreate(full_name="Ativo", document_number="111")
    )
    blocked_passenger = await passenger_service.create_passenger(
        PassengerCreate(full_name="Bloqueado", document_number="222")
    )
    await passenger_service.block_passenger(blocked_passenger.id)

    now = datetime.now(timezone.utc)
    await ticket_service.create_ticket(
        TicketCreate(
            passenger_id=active_passenger.id,
            valid_from=now,
            valid_until=now + timedelta(days=1),
        )
    )

    sync_service = await _build_sync_service(db_session)
    response = await sync_service.pull(device_id="bus-01", since=None)

    assert [p.id for p in response.passengers] == [active_passenger.id]
    assert len(response.tickets) == 1
    assert response.tickets[0].passenger_id == active_passenger.id

    status = await sync_service.status("bus-01")
    assert status.registered is True
    assert status.last_pull_at is not None


async def test_pull_includes_revoked_embeddings_with_active_flag(
    db_session: AsyncSession,
) -> None:
    """
    Regression test for the biometric-revocation propagation bug: a
    revoked embedding (active=False) must still be sent on an incremental
    pull, tagged with `active=False`, so the edge can drop it from its
    local match candidates. The actual SQL filter on
    `FaceEmbeddingRepository.list_active` can't be exercised against the
    SQLite test DB (pgvector columns aren't supported there — see
    conftest.py), so this test instead pins down the contract at the
    service/schema boundary: whatever the repository returns, `active`
    must flow through unchanged into `EmbeddingSyncItem`.
    """
    sync_service = await _build_sync_service(db_session)

    revoked_embedding = SimpleNamespace(
        id=uuid.uuid4(),
        passenger_id=uuid.uuid4(),
        embedding=[0.1, 0.2, 0.3],
        model_name="arcface",
        model_version="r100",
        active=False,
    )
    sync_service.embedding_repository.list_active = AsyncMock(
        return_value=[revoked_embedding]
    )

    response = await sync_service.pull(device_id="bus-04", since=datetime.now(timezone.utc))

    assert len(response.embeddings) == 1
    assert response.embeddings[0].id == revoked_embedding.id
    assert response.embeddings[0].active is False


async def test_push_delegates_to_validation_service_and_updates_state(
    db_session: AsyncSession,
) -> None:
    sync_service = await _build_sync_service(db_session)

    event = ValidationEventIngest(
        external_id="evt-sync-1",
        bus_id="bus-02",
        status=ValidationStatus.AUTHORIZED,
        captured_at=datetime.now(timezone.utc),
    )

    response = await sync_service.push(device_id="bus-02", events=[event])

    assert response.accepted == ["evt-sync-1"]
    assert response.device_id == "bus-02"

    status = await sync_service.status("bus-02")
    assert status.last_push_at is not None


async def test_ack_persists_cursor(db_session: AsyncSession) -> None:
    sync_service = await _build_sync_service(db_session)
    cursor = datetime.now(timezone.utc)

    response = await sync_service.ack(device_id="bus-03", cursor=cursor)

    assert response.device_id == "bus-03"

    status = await sync_service.status("bus-03")
    # SQLite (used only in this test DB) drops tzinfo on round-trip; Postgres
    # preserves it. Compare naive fields directly to avoid local-tz bias.
    assert status.last_pull_cursor.replace(tzinfo=None) == cursor.replace(tzinfo=None)


async def test_status_for_unknown_device_is_not_an_error(db_session: AsyncSession) -> None:
    sync_service = await _build_sync_service(db_session)

    status = await sync_service.status("never-seen-before")

    assert status.registered is False
    assert status.last_pull_at is None


async def test_list_devices_returns_all_registered_devices(db_session: AsyncSession) -> None:
    sync_service = await _build_sync_service(db_session)

    await sync_service.ack(device_id="bus-10", cursor=datetime.now(timezone.utc))
    await sync_service.ack(device_id="bus-20", cursor=datetime.now(timezone.utc))

    result = await sync_service.list_devices()

    device_ids = {device.device_id for device in result.devices}
    assert {"bus-10", "bus-20"}.issubset(device_ids)
    assert all(device.registered for device in result.devices)


async def test_list_devices_with_none_registered_is_empty(db_session: AsyncSession) -> None:
    sync_service = await _build_sync_service(db_session)

    result = await sync_service.list_devices()

    assert result.devices == []
