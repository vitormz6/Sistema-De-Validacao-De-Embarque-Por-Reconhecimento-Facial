"""create local_validation_logs table

Revision ID: 20260621_0004
Revises: 20260621_0003
Create Date: 2026-06-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260621_0004"
down_revision: Union[str, None] = "20260621_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "local_validation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("bus_id", sa.String(length=64), nullable=False),
        sa.Column("route_id", sa.String(length=64), nullable=True),
        sa.Column(
            "passenger_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("local_passengers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "ticket_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("local_tickets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("similarity_distance", sa.Float(), nullable=True),
        sa.Column("reason_code", sa.String(length=60), nullable=True),
        sa.Column("is_offline", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index("ix_local_validation_logs_bus_id", "local_validation_logs", ["bus_id"], unique=False)
    op.create_index(
        "ix_local_validation_logs_passenger_id",
        "local_validation_logs",
        ["passenger_id"],
        unique=False,
    )
    op.create_index("ix_local_validation_logs_status", "local_validation_logs", ["status"], unique=False)
    op.create_index(
        "ix_local_validation_logs_synced_at", "local_validation_logs", ["synced_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_local_validation_logs_synced_at", table_name="local_validation_logs")
    op.drop_index("ix_local_validation_logs_status", table_name="local_validation_logs")
    op.drop_index("ix_local_validation_logs_passenger_id", table_name="local_validation_logs")
    op.drop_index("ix_local_validation_logs_bus_id", table_name="local_validation_logs")
    op.drop_table("local_validation_logs")
