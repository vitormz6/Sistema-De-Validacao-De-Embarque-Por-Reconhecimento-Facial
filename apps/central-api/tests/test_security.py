import uuid

import pytest

from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
    verify_edge_device_key,
)
from app.core.config import settings


def test_hash_password_does_not_store_plaintext() -> None:
    hashed = hash_password("super-secret")
    assert hashed != "super-secret"
    assert verify_password("super-secret", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_roundtrip() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id, extra_claims={"role": "ADMIN"})

    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["role"] == "ADMIN"


def test_decode_access_token_rejects_garbage() -> None:
    with pytest.raises(UnauthorizedError):
        decode_access_token("not-a-real-token")


def test_verify_edge_device_key_accepts_configured_key() -> None:
    # Should not raise.
    verify_edge_device_key(x_device_key=settings.EDGE_SYNC_API_KEY)


def test_verify_edge_device_key_rejects_wrong_key() -> None:
    with pytest.raises(UnauthorizedError):
        verify_edge_device_key(x_device_key="wrong-key")


def test_verify_edge_device_key_rejects_missing_key() -> None:
    with pytest.raises(UnauthorizedError):
        verify_edge_device_key(x_device_key=None)
