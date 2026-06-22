"""create boarding_validations table

Revision ID: 20260621_0006
Revises: 20260621_0005
Create Date: 2026-06-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260621_0006"
down_revision: Union[str, None] = "20260621_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "boarding_validations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("bus_id", sa.String(length=64), nullable=False),
        sa.Column("route_id", sa.String(length=64), nullable=True),
        sa.Column(
            "passenger_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("passengers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "ticket_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tickets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("similarity_distance", sa.Float(), nullable=True),
        sa.Column("reason_code", sa.String(length=60), nullable=True),
        sa.Column("is_offline", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_boarding_validations_external_id",
        "boarding_validations",
        ["external_id"],
        unique=True,
    )
    op.create_index(
        "ix_boarding_validations_bus_id", "boarding_validations", ["bus_id"], unique=False
    )
    op.create_index(
        "ix_boarding_validations_passenger_id",
        "boarding_validations",
        ["passenger_id"],
        unique=False,
    )
    op.create_index(
        "ix_boarding_validations_status", "boarding_validations", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_boarding_validations_status", table_name="boarding_validations")
    op.drop_index("ix_boarding_validations_passenger_id", table_name="boarding_validations")
    op.drop_index("ix_boarding_validations_bus_id", table_name="boarding_validations")
    op.drop_index("ix_boarding_validations_external_id", table_name="boarding_validations")
    op.drop_table("boarding_validations")
