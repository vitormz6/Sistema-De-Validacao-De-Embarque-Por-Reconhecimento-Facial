# Verifica se o ônibus tem conexão com a central e guarda o último resultado em cache.
# O check real só roda quando o health endpoint é chamado — na validação de embarque
# só lê o cache pra não adicionar latência.
# Por padrão assume offline até o primeiro check.
# TODO: talvez seja melhor rodar o check em background periodicamente

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
