"""create passengers table

Revision ID: 20260617_0001
Revises:
Create Date: 2026-06-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260617_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "passengers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "full_name",
            sa.String(length=160),
            nullable=False,
        ),
        sa.Column(
            "document_number",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "birth_date",
            sa.Date(),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_passengers_full_name",
        "passengers",
        ["full_name"],
        unique=False,
    )

    op.create_index(
        "ix_passengers_document_number",
        "passengers",
        ["document_number"],
        unique=True,
    )

    op.create_index(
        "ix_passengers_status",
        "passengers",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_passengers_status", table_name="passengers")
    op.drop_index("ix_passengers_document_number", table_name="passengers")
    op.drop_index("ix_passengers_full_name", table_name="passengers")
    op.drop_table("passengers")