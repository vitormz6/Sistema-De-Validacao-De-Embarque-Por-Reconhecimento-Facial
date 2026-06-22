"""
HTTP client for the `vision-service`.

The vision-service owns face detection, quality assessment and embedding
generation (SCRFD + ArcFace, see README2 section 3.2). The central-api never
runs inference itself — it always delegates to this service, keeping the
"IA isolada" boundary defined in the architecture.

NOTE: `vision-service` is not implemented yet (next module to build). This
client encodes the contract the central-api expects from it so biometrics
enrollment/compare can be developed and tested against a fake/mocked client
in the meantime.
"""

from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.core.exceptions import UpstreamServiceError


@dataclass(frozen=True, slots=True)
class FaceEmbeddingResult:
    face_found: bool
    embedding: list[float] | None
    quality_score: float | None
    model_name: str | None
    model_version: str | None
    detector_name: str | None
    detector_version: str | None
    reason: str | None = None
    # Basic liveness heuristic (RFC 3.4 - R2/M6). Defaulted so older
    # vision-service payloads / existing test fixtures without these keys
    # stay valid — absence is treated as "no liveness signal available",
    # not as a pass.
    liveness_score: float | None = None
    spoof_suspected: bool | None = None


class VisionServiceClient:
    """Thin async wrapper around the vision-service HTTP API."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = base_url or settings.VISION_SERVICE_URL
        self.timeout_seconds = timeout_seconds or settings.VISION_SERVICE_TIMEOUT_SECONDS

    async def detect_and_embed(self, image_bytes: bytes, content_type: str) -> FaceEmbeddingResult:
        """
        Sends an image to the vision-service and returns the detected face's
        embedding plus quality metadata.

        Expected contract: `POST /embeddings/generate` (multipart, field
        "file") -> 200 with
        `{face_found, embedding, quality_score, model_name, model_version,
        detector_name, detector_version, reason}`.
        """
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout_seconds
            ) as client:
                response = await client.post(
                    "/embeddings/generate",
                    files={"file": ("probe.jpg", image_bytes, content_type)},
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise UpstreamServiceError(
                "Unable to reach vision-service for face detection/embedding."
            ) from exc

        return FaceEmbeddingResult(
            face_found=payload.get("face_found", False),
            embedding=payload.get("embedding"),
            quality_score=payload.get("quality_score"),
            model_name=payload.get("model_name"),
            model_version=payload.get("model_version"),
            detector_name=payload.get("detector_name"),
            detector_version=payload.get("detector_version"),
            reason=payload.get("reason"),
            liveness_score=payload.get("liveness_score"),
            spoof_suspected=payload.get("spoof_suspected"),
        )
