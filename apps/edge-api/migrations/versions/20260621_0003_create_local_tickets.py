"""create local_tickets table

Revision ID: 20260621_0003
Revises: 20260621_0002
Create Date: 2026-06-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260621_0003"
down_revision: Union[str, None] = "20260621_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "local_tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "passenger_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("local_passengers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ticket_type", sa.String(length=30), nullable=False, server_default="SINGLE"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index("ix_local_tickets_passenger_id", "local_tickets", ["passenger_id"], unique=False)
    op.create_index("ix_local_tickets_status", "local_tickets", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_local_tickets_status", table_name="local_tickets")
    op.drop_index("ix_local_tickets_passenger_id", table_name="local_tickets")
    op.drop_table("local_tickets")
