"""enable pgvector extension

Revision ID: 20260621_0002
Revises: 20260617_0001
Create Date: 2026-06-21

"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260621_0002"
down_revision: Union[str, None] = "20260617_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
