# Funções de segurança: hash de senha, JWT e verificação da chave do edge.

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import Header
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.core.exceptions import UnauthorizedError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

JWT_SUBJECT_CLAIM = "sub"


def hash_password(plain_password: str) -> str:
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: uuid.UUID, extra_claims: dict[str, Any] | None = None) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        JWT_SUBJECT_CLAIM: str(subject),
        "iat": now,
        "exp": expires_at,
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired access token.") from exc


def verify_edge_device_key(x_device_key: str | None = Header(default=None)) -> None:
    """Dependência FastAPI que valida a chave compartilhada do sync-worker."""
    if not x_device_key or x_device_key != settings.EDGE_SYNC_API_KEY:
        raise UnauthorizedError("Invalid or missing edge device key.")
