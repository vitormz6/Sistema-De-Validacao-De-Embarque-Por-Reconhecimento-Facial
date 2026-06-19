from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def import_all_models() -> None:
    """
    Imports all SQLAlchemy models so Alembic can detect metadata changes.
    """
    from app.modules.passengers.model import Passenger  # noqa: F401