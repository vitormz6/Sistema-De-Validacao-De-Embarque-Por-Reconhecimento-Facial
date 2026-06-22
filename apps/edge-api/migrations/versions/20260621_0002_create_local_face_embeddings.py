"""create local_face_embeddings table

Revision ID: 20260621_0002
Revises: 20260621_0001
Create Date: 2026-06-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260621_0002"
down_revision: Union[str, None] = "20260621_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "local_face_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "passenger_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("local_passengers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=False),
        sa.Column("model_name", sa.String(length=60), nullable=False),
        sa.Column("model_version", sa.String(length=60), nullable=False),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_local_face_embeddings_passenger_id",
        "local_face_embeddings",
        ["passenger_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_local_face_embeddings_passenger_id", table_name="local_face_embeddings")
    op.drop_table("local_face_embeddings")
