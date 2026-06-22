import uuid

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import JWT_SUBJECT_CLAIM, decode_access_token, oauth2_scheme
from app.database.session import get_db_session
from app.modules.auth.model import User
from app.modules.auth.repository import UserRepository
from app.shared.enums import UserRole


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    if not token:
        raise UnauthorizedError("Missing access token.")

    payload = decode_access_token(token)
    raw_user_id = payload.get(JWT_SUBJECT_CLAIM)

    if raw_user_id is None:
        raise UnauthorizedError("Invalid access token payload.")

    try:
        user_id = uuid.UUID(raw_user_id)
    except ValueError as exc:
        raise UnauthorizedError("Invalid access token subject.") from exc

    repository = UserRepository(session)
    user = await repository.get_by_id(user_id)

    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive.")

    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN.value:
        raise ForbiddenError("This action requires administrator privileges.")

    return user
