import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.database.base import Base


class FaceEmbedding(Base):
    """
    Embedding facial de um passageiro. Só um pode estar active=True por vez.
    Novo cadastro revoga o anterior em vez de deletar (mantém histórico).
    """

    __tablename__ = "face_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    passenger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("passengers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.EMBEDDING_DIMENSIONS),
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(String(60), nullable=False)
    model_version: Mapped[str] = mapped_column(String(60), nullable=False)
    detector_name: Mapped[str] = mapped_column(String(60), nullable=False)
    detector_version: Mapped[str] = mapped_column(String(60), nullable=False)

    quality_score: Mapped[float] = mapped_column(Float, nullable=False)

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
