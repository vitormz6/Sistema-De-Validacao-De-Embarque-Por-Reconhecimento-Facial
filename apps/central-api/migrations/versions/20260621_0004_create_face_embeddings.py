"""create face_embeddings table

Revision ID: 20260621_0004
Revises: 20260621_0003
Create Date: 2026-06-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from app.core.config import settings

revision: str = "20260621_0004"
down_revision: Union[str, None] = "20260621_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "face_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "passenger_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("passengers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("embedding", Vector(settings.EMBEDDING_DIMENSIONS), nullable=False),
        sa.Column("model_name", sa.String(length=60), nullable=False),
        sa.Column("model_version", sa.String(length=60), nullable=False),
        sa.Column("detector_name", sa.String(length=60), nullable=False),
        sa.Column("detector_version", sa.String(length=60), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        "ix_face_embeddings_passenger_id", "face_embeddings", ["passenger_id"], unique=False
    )
    op.create_index("ix_face_embeddings_active", "face_embeddings", ["active"], unique=False)

    # Approximate nearest-neighbor index for cosine distance lookups used by
    # the biometrics "compare" flow. HNSW chosen over IVFFlat for better
    # recall at the MVP's expected (small) dataset size.
    op.execute(
        "CREATE INDEX ix_face_embeddings_embedding_cosine "
        "ON face_embeddings USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_face_embeddings_embedding_cosine")
    op.drop_index("ix_face_embeddings_active", table_name="face_embeddings")
    op.drop_index("ix_face_embeddings_passenger_id", table_name="face_embeddings")
    op.drop_table("face_embeddings")
