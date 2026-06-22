import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationFailedError
from app.modules.biometrics.model import FaceEmbedding
from app.modules.biometrics.repository import FaceEmbeddingRepository
from app.modules.biometrics.schema import BiometricCompareResult
from app.modules.biometrics.vision_client import VisionServiceClient
from app.modules.passengers.repository import PassengerRepository
from app.shared.enums import ValidationStatus


class BiometricService:
    def __init__(
        self,
        session: AsyncSession,
        vision_client: VisionServiceClient | None = None,
    ) -> None:
        self.session = session
        self.repository = FaceEmbeddingRepository(session)
        self.passenger_repository = PassengerRepository(session)
        self.vision_client = vision_client or VisionServiceClient()

    async def enroll(
        self,
        passenger_id: uuid.UUID,
        image_bytes: bytes,
        content_type: str,
    ) -> FaceEmbedding:
        passenger = await self.passenger_repository.get_by_id(passenger_id)

        if passenger is None:
            raise NotFoundError("Passenger not found.")

        result = await self.vision_client.detect_and_embed(image_bytes, content_type)

        if not result.face_found or result.embedding is None:
            raise ValidationFailedError(
                result.reason or "No face was detected in the provided image."
            )

        if result.quality_score is None or result.quality_score < settings.MIN_FACE_QUALITY_SCORE:
            raise ValidationFailedError(
                "Image quality is below the minimum required threshold for enrollment."
            )

        if result.spoof_suspected:
            raise ValidationFailedError(
                "Possible spoofing attempt detected (liveness check failed)."
            )

        await self.repository.revoke_active(passenger_id)

        embedding = FaceEmbedding(
            passenger_id=passenger_id,
            embedding=result.embedding,
            model_name=result.model_name or "unknown",
            model_version=result.model_version or "unknown",
            detector_name=result.detector_name or "unknown",
            detector_version=result.detector_version or "unknown",
            quality_score=result.quality_score,
            active=True,
        )

        created_embedding = await self.repository.create(embedding)
        await self.session.commit()

        return created_embedding

    async def list_history(self, passenger_id: uuid.UUID) -> list[FaceEmbedding]:
        passenger = await self.passenger_repository.get_by_id(passenger_id)

        if passenger is None:
            raise NotFoundError("Passenger not found.")

        return await self.repository.list_by_passenger(passenger_id)

    async def revoke(self, passenger_id: uuid.UUID) -> FaceEmbedding:
        active_embedding = await self.repository.get_active_by_passenger(passenger_id)

        if active_embedding is None:
            raise NotFoundError("Passenger has no active biometric enrollment.")

        await self.repository.revoke_active(passenger_id)
        await self.session.commit()
        await self.session.refresh(active_embedding)

        return active_embedding

    async def compare(
        self,
        image_bytes: bytes,
        content_type: str,
        passenger_id: uuid.UUID | None = None,
    ) -> BiometricCompareResult:
        result = await self.vision_client.detect_and_embed(image_bytes, content_type)

        if not result.face_found or result.embedding is None:
            return BiometricCompareResult(
                decision=ValidationStatus.DENIED_FACE_NOT_FOUND.value,
                matched_passenger_id=None,
                distance=None,
                similarity=None,
                threshold=settings.MAX_SIMILARITY_DISTANCE,
            )

        if result.spoof_suspected:
            return BiometricCompareResult(
                decision=ValidationStatus.DENIED_SPOOF_SUSPECTED.value,
                matched_passenger_id=None,
                distance=None,
                similarity=None,
                threshold=settings.MAX_SIMILARITY_DISTANCE,
            )

        matches = await self.repository.find_nearest(
            result.embedding,
            passenger_id=passenger_id,
            limit=1,
        )

        if not matches:
            return BiometricCompareResult(
                decision=ValidationStatus.DENIED_LOW_CONFIDENCE.value,
                matched_passenger_id=None,
                distance=None,
                similarity=None,
                threshold=settings.MAX_SIMILARITY_DISTANCE,
            )

        matched_embedding, distance = matches[0]
        similarity = max(0.0, 1.0 - distance)
        is_match = distance <= settings.MAX_SIMILARITY_DISTANCE

        return BiometricCompareResult(
            decision=(
                ValidationStatus.AUTHORIZED.value
                if is_match
                else ValidationStatus.DENIED_LOW_CONFIDENCE.value
            ),
            matched_passenger_id=matched_embedding.passenger_id if is_match else None,
            distance=distance,
            similarity=similarity,
            threshold=settings.MAX_SIMILARITY_DISTANCE,
        )
