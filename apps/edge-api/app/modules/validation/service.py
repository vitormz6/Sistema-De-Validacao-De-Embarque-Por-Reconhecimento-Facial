from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.connectivity import ConnectivityTracker, get_connectivity_tracker
from app.modules.cache.matching import find_nearest
from app.modules.cache.repository import (
    EmbeddingCacheRepository,
    PassengerCacheRepository,
    TicketCacheRepository,
)
from app.modules.cache.vision_client import VisionServiceClient
from app.modules.validation.model import LocalValidationLog
from app.modules.validation.repository import ValidationLogRepository
from app.modules.validation.schema import BoardingValidationResponse
from app.shared.enums import PassengerStatus, ValidationStatus

REASON_NO_FACE_DETECTED = "NO_FACE_DETECTED"
REASON_SPOOF_SUSPECTED = "SPOOF_SUSPECTED"
REASON_LOW_QUALITY = "LOW_QUALITY"
REASON_NO_MATCH_WITHIN_THRESHOLD = "NO_MATCH_WITHIN_THRESHOLD"
REASON_PASSENGER_BLOCKED = "PASSENGER_BLOCKED"
REASON_NO_ACTIVE_TICKET = "NO_ACTIVE_TICKET"


class BoardingValidationService:
    """
    The RF07/RF08/RF09 decision pipeline: everything it touches is local
    (this DB + the on-bus vision-service) — no call to central-api ever
    sits on this path, which is what actually makes boarding validation
    offline-first rather than just "offline-tolerant".
    """

    def __init__(
        self,
        session: AsyncSession,
        vision_client: VisionServiceClient | None = None,
        connectivity_tracker: ConnectivityTracker | None = None,
    ) -> None:
        self.session = session
        self.passenger_repository = PassengerCacheRepository(session)
        self.embedding_repository = EmbeddingCacheRepository(session)
        self.ticket_repository = TicketCacheRepository(session)
        self.log_repository = ValidationLogRepository(session)
        self.vision_client = vision_client or VisionServiceClient()
        self.connectivity_tracker = connectivity_tracker or get_connectivity_tracker()

    async def validate(self, image_bytes: bytes, content_type: str) -> BoardingValidationResponse:
        captured_at = datetime.now(timezone.utc)
        is_offline = self.connectivity_tracker.is_offline

        result = await self.vision_client.detect_and_embed(image_bytes, content_type)

        status = ValidationStatus.DENIED_FACE_NOT_FOUND
        reason_code: str | None = None
        confidence_score: float | None = None
        similarity_distance: float | None = None
        passenger = None
        ticket = None

        if not result.face_found or result.embedding is None:
            status = ValidationStatus.DENIED_FACE_NOT_FOUND
            reason_code = result.reason or REASON_NO_FACE_DETECTED

        elif result.spoof_suspected:
            status = ValidationStatus.DENIED_SPOOF_SUSPECTED
            reason_code = REASON_SPOOF_SUSPECTED

        elif result.quality_score is not None and result.quality_score < settings.MIN_FACE_QUALITY_SCORE:
            status = ValidationStatus.DENIED_LOW_CONFIDENCE
            reason_code = REASON_LOW_QUALITY

        else:
            candidates = await self.embedding_repository.list_active()
            match = find_nearest(result.embedding, candidates)

            if match is not None:
                similarity_distance = match.distance
                confidence_score = max(0.0, 1.0 - match.distance)

            if match is None or match.distance > settings.MAX_SIMILARITY_DISTANCE:
                status = ValidationStatus.DENIED_LOW_CONFIDENCE
                reason_code = REASON_NO_MATCH_WITHIN_THRESHOLD

            else:
                passenger = await self.passenger_repository.get_by_id(match.passenger_id)

                if passenger is None or passenger.status == PassengerStatus.BLOCKED.value:
                    status = ValidationStatus.DENIED_PASSENGER_BLOCKED
                    reason_code = REASON_PASSENGER_BLOCKED
                else:
                    ticket = await self.ticket_repository.get_active_for_passenger(
                        passenger.id, now=captured_at
                    )

                    if ticket is None:
                        status = ValidationStatus.DENIED_NO_ACTIVE_TICKET
                        reason_code = REASON_NO_ACTIVE_TICKET
                    else:
                        status = ValidationStatus.AUTHORIZED
                        reason_code = None

        log = LocalValidationLog(
            bus_id=settings.BUS_ID,
            passenger_id=passenger.id if passenger else None,
            ticket_id=ticket.id if ticket else None,
            status=status.value,
            confidence_score=confidence_score,
            similarity_distance=similarity_distance,
            reason_code=reason_code,
            is_offline=is_offline,
            captured_at=captured_at,
        )

        created_log = await self.log_repository.create(log)
        await self.session.commit()

        return BoardingValidationResponse(
            id=created_log.id,
            status=status,
            passenger_id=passenger.id if passenger else None,
            passenger_name=passenger.full_name if passenger else None,
            ticket_id=ticket.id if ticket else None,
            confidence_score=confidence_score,
            similarity_distance=similarity_distance,
            reason_code=reason_code,
            is_offline=is_offline,
            captured_at=captured_at,
        )
