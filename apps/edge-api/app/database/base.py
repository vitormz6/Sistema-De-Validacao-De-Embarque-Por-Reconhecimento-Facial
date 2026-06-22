from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def import_all_models() -> None:
    """
    Imports all SQLAlchemy models so Alembic can detect metadata changes.
    """
    from app.modules.cache.model import LocalFaceEmbedding, LocalPassenger, LocalTicket  # noqa: F401
    from app.modules.validation.model import LocalValidationLog  # noqa: F401
