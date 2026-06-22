"""create local_sync_state table

Revision ID: 20260621_0005
Revises: 20260621_0004
Create Date: 2026-06-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260621_0005"
down_revision: Union[str, None] = "20260621_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "local_sync_state",
        sa.Column("device_id", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("last_pull_cursor", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("local_sync_state")
