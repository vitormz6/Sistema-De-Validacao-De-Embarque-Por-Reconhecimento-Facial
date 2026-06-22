from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Maps onto the SAME postgres-edge schema edge-api owns and migrates
    (see apps/edge-api/migrations). This worker never runs migrations of
    its own — it only reads/writes tables that already exist.
    """


def import_all_models() -> None:
    """Imports all SQLAlchemy models so metadata is fully populated for
    tests (see tests/conftest.py)."""
    from app.modules.cache.model import LocalFaceEmbedding, LocalPassenger, LocalTicket  # noqa: F401
    from app.modules.sync_state.model import LocalSyncState  # noqa: F401
    from app.modules.validation.model import LocalValidationLog  # noqa: F401
