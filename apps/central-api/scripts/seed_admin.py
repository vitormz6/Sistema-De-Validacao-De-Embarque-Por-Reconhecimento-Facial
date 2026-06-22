"""
Bootstraps the first administrator user.

There is no public registration endpoint on purpose (RNF03 - controle de
acesso): `POST /auth/users` requires an authenticated admin, which creates a
chicken-and-egg problem for the very first account. Run this script once
against the central database to break that cycle.

Usage (from apps/central-api, with the virtualenv active and DATABASE_URL
pointed at the central Postgres instance):

    python -m scripts.seed_admin --email admin@example.com --password change-me --name "Admin"
"""

import argparse
import asyncio

from app.database.session import AsyncSessionLocal
from app.modules.auth.schema import UserCreate
from app.modules.auth.service import AuthService
from app.shared.enums import UserRole


async def seed_admin(email: str, password: str, full_name: str) -> None:
    async with AsyncSessionLocal() as session:
        service = AuthService(session)
        user = await service.create_user(
            UserCreate(
                email=email,
                password=password,
                full_name=full_name,
                role=UserRole.ADMIN,
            )
        )
        print(f"Admin user created: {user.id} <{user.email}>")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the first admin user.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", required=True, dest="full_name")
    args = parser.parse_args()

    asyncio.run(seed_admin(args.email, args.password, args.full_name))


if __name__ == "__main__":
    main()
