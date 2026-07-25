from app.db.session import Base
# Import all SQLAlchemy models here so Alembic and init_db can discover them
from app.models.invoice import Invoice  # noqa: F401
