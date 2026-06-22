from unittest.mock import AsyncMock, patch

import httpx

from app.core.connectivity import ConnectivityTracker


def test_defaults_to_offline_before_any_check() -> None:
    tracker = ConnectivityTracker()

    assert tracker.is_offline is True
    assert tracker.checked_at is None


async def test_check_now_marks_offline_when_unreachable() -> None:
    tracker = ConnectivityTracker()

    # Mocked rather than pointed at a real unreachable address: exercises
    # the httpx.HTTPError branch hermetically, regardless of whatever
    # proxy/network env vars the runner happens to have set.
    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=httpx.ConnectError("boom"))):
        is_online = await tracker.check_now()

    assert is_online is False
    assert tracker.is_offline is True
    assert tracker.checked_at is not None


async def test_check_now_marks_online_on_success() -> None:
    tracker = ConnectivityTracker()

    fake_response = httpx.Response(200, request=httpx.Request("GET", "http://central-api/health"))

    with patch("httpx.AsyncClient.get", new=AsyncMock(return_value=fake_response)):
        is_online = await tracker.check_now()

    assert is_online is True
    assert tracker.is_offline is False
    assert tracker.checked_at is not None
