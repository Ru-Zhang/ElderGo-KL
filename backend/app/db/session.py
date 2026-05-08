from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


settings = get_settings()
# Keep one process-level engine/session factory; request handlers receive
# short-lived sessions through `get_db`.
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    # FastAPI dependency that guarantees session cleanup after each request.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
