import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.core.config import settings
from app.modules.auth.model import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schema import LoginRequest, TokenResponse, UserCreate


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)

    async def create_user(self, data: UserCreate) -> User:
        if await self.repository.exists_by_email(data.email):
            raise ConflictError("A user with this email already exists.")

        user = User(
            email=data.email.lower().strip(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name.strip(),
            role=data.role.value,
            is_active=True,
        )

        created_user = await self.repository.create(user)
        await self.session.commit()

        return created_user

    async def authenticate(self, data: LoginRequest) -> User:
        user = await self.repository.get_by_email(data.email.lower().strip())

        if user is None or not user.is_active or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password.")

        return user

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        return await self.repository.get_by_id(user_id)

    def issue_token(self, user: User) -> TokenResponse:
        access_token = create_access_token(subject=user.id, extra_claims={"role": user.role})

        return TokenResponse(
            access_token=access_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
