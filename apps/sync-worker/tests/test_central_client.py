from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.central_client import CentralApiClient
from app.core.exceptions import SyncUpstreamError


def _fake_response(json_body: dict, status_code: int = 200) -> httpx.Response:
    request = httpx.Request("POST", "http://central-api/sync/pull")
    return httpx.Response(status_code, json=json_body, request=request)


async def test_pull_parses_response_into_pull_result() -> None:
    body = {
        "device_id": "bus-01",
        "generated_at": "2026-06-21T12:00:00Z",
        "cursor": "2026-06-21T12:00:00Z",
        "passengers": [],
        "embeddings": [],
        "tickets": [],
    }

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_fake_response(body))):
        client = CentralApiClient(api_key="secret")
        result = await client.pull(since=None)

    assert result.cursor == datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)
    assert result.passengers == []


async def test_pull_raises_sync_upstream_error_on_http_error() -> None:
    with patch(
        "httpx.AsyncClient.post", new=AsyncMock(side_effect=httpx.ConnectError("boom"))
    ):
        client = CentralApiClient(api_key="secret")
        with pytest.raises(SyncUpstreamError):
            await client.pull(since=None)


async def test_push_parses_accepted_duplicated_rejected() -> None:
    body = {
        "device_id": "bus-01",
        "accepted": ["a"],
        "duplicated": ["b"],
        "rejected": [{"external_id": "c", "reason": "invalid"}],
    }

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=_fake_response(body))):
        client = CentralApiClient(api_key="secret")
        result = await client.push(events=[])

    assert result.accepted == ["a"]
    assert result.duplicated == ["b"]
    assert result.rejected == [{"external_id": "c", "reason": "invalid"}]


async def test_ack_raises_on_non_2xx_status() -> None:
    error_response = _fake_response({"detail": "nope"}, status_code=401)

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=error_response)):
        client = CentralApiClient(api_key="wrong-key")
        with pytest.raises(SyncUpstreamError):
            await client.ack(cursor=datetime.now(timezone.utc))
