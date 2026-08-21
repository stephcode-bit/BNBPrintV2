from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()

# psycopg2 sync engine — simple and reliable for a service this size.
# Railway/most Postgres hosts give a `postgresql://` URL; SQLAlchemy 2.x
# wants the `postgresql+psycopg2://` scheme, so normalize it here.
_url = settings.database_url
if _url.startswith("postgresql://"):
    _url = _url.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(_url, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables if they don't exist. Fine for this project's scale;
    swap for Alembic migrations if the schema starts changing often."""
    from app import models  # noqa: F401 (ensures models are registered)

    Base.metadata.create_all(bind=engine)
