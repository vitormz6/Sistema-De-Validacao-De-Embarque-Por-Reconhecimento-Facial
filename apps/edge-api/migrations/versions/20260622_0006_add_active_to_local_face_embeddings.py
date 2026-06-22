"""add active column to local_face_embeddings

Revision ID: 20260622_0006
Revises: 20260621_0005
Create Date: 2026-06-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260622_0006"
down_revision: Union[str, None] = "20260621_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "local_face_embeddings",
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.create_index(
        "ix_local_face_embeddings_active",
        "local_face_embeddings",
        ["active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_local_face_embeddings_active", table_name="local_face_embeddings")
    op.drop_column("local_face_embeddings", "active")
