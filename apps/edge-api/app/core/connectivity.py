"""
Tracks whether this bus currently has a path to the central API, without
putting a network round-trip on the boarding-validation hot path (RNF01
wants a decision in ≤2s; blocking on a possibly-timing-out ping to a
central server that might be unreachable would defeat that).

`check_now()` does the actual HTTP probe and is meant to be called from the
health endpoint (RF14) — whatever cadence the operator UI polls
`/local/device/status` at is the connectivity check's effective frequency.
`is_offline` just reads the last cached result; until the first check ever
runs, it conservatively defaults to True (assume offline rather than
optimistically AUTHORIZED-tag attempts as online).
"""

from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from app.core.config import settings


@dataclass
class _ConnectivityState:
    is_online: bool = False
    checked_at: datetime | None = None
    last_error: str | None = None


class ConnectivityTracker:
    def __init__(self) -> None:
        self._state = _ConnectivityState()

    @property
    def is_offline(self) -> bool:
        return not self._state.is_online

    @property
    def checked_at(self) -> datetime | None:
        return self._state.checked_at

    async def check_now(self) -> bool:
        try:
            # trust_env=False: this is a fixed, internally-known service URL,
            # not a browser-style outbound request — it shouldn't depend on
            # whatever ambient HTTP_PROXY/ALL_PROXY env vars happen to be set
            # on the host (and avoids requiring optional SOCKS extras just to
            # reach a sibling container).
            async with httpx.AsyncClient(
                base_url=settings.CENTRAL_API_URL,
                timeout=settings.CENTRAL_API_PING_TIMEOUT_SECONDS,
                trust_env=False,
            ) as client:
                response = await client.get("/health")
                response.raise_for_status()
                self._state = _ConnectivityState(is_online=True, checked_at=_now())
        except httpx.HTTPError as exc:
            self._state = _ConnectivityState(
                is_online=False, checked_at=_now(), last_error=str(exc)
            )

        return self._state.is_online


def _now() -> datetime:
    return datetime.now(timezone.utc)


_tracker: ConnectivityTracker | None = None


def get_connectivity_tracker() -> ConnectivityTracker:
    global _tracker
    if _tracker is None:
        _tracker = ConnectivityTracker()
    return _tracker
