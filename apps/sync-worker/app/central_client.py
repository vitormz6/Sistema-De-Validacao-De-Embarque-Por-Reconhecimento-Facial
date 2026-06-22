from datetime import datetime

import httpx

from app.core.config import settings
from app.core.exceptions import SyncUpstreamError
from app.schemas import PullResult, PushResult


class CentralApiClient:
    """
    Thin async wrapper around central-api's `/sync/*` endpoints
    (`app/modules/sync/router.py`), authenticated with the shared
    `X-Device-Key` header (`verify_edge_device_key`) rather than a user
    JWT — this worker isn't acting on behalf of an admin, it's the device
    itself.
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        device_id: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.base_url = base_url or settings.CENTRAL_API_URL
        self.timeout_seconds = timeout_seconds or settings.CENTRAL_API_TIMEOUT_SECONDS
        self.device_id = device_id or settings.BUS_ID
        self.api_key = api_key or settings.EDGE_SYNC_API_KEY

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            trust_env=False,
            headers={"X-Device-Key": self.api_key},
        )

    async def pull(self, since: datetime | None) -> PullResult:
        body = {"device_id": self.device_id, "since": since.isoformat() if since else None}

        try:
            async with self._client() as client:
                response = await client.post("/sync/pull", json=body)
                response.raise_for_status()
                return PullResult.model_validate(response.json())
        except httpx.HTTPError as exc:
            raise SyncUpstreamError(f"Failed to pull from central-api: {exc}") from exc

    async def push(self, events: list[dict]) -> PushResult:
        body = {"device_id": self.device_id, "events": events}

        try:
            async with self._client() as client:
                response = await client.post("/sync/push", json=body)
                response.raise_for_status()
                return PushResult.model_validate(response.json())
        except httpx.HTTPError as exc:
            raise SyncUpstreamError(f"Failed to push to central-api: {exc}") from exc

    async def ack(self, cursor: datetime) -> None:
        body = {"device_id": self.device_id, "cursor": cursor.isoformat()}

        try:
            async with self._client() as client:
                response = await client.post("/sync/ack", json=body)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SyncUpstreamError(f"Failed to ack pull cursor on central-api: {exc}") from exc
