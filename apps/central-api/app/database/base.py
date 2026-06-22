from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def import_all_models() -> None:
    """
    Imports all SQLAlchemy models so Alembic can detect metadata changes.
    """
    from app.modules.auth.model import User  # noqa: F401
    from app.modules.biometrics.model import FaceEmbedding  # noqa: F401
    from app.modules.passengers.model import Passenger  # noqa: F401
    from app.modules.sync.model import SyncDeviceState  # noqa: F401
    from app.modules.tickets.model import Ticket  # noqa: F401
    from app.modules.validations.model import BoardingValidation  # noqa: F401