"""Database engine and session management for AdaptLearn.

Requirements Traceability:
- NFR-07: Parameterized queries / ORM mapping.
- NFR-08: Transactional integrity and atomic commits.
- Decision D6: SQLAlchemy 2.0 ORM with PostgreSQL-compatible architecture.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base


def get_engine_args(db_url: str) -> dict:
    """Return dialect-appropriate engine arguments."""
    if db_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


# Default application engine and session factory
engine = create_engine(settings.DATABASE_URL, **get_engine_args(settings.DATABASE_URL))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(target_engine=None) -> None:
    """Create all database tables if they do not exist."""
    import app.models  # noqa: F401 - ensure models register with Base.metadata

    e = target_engine or engine
    Base.metadata.create_all(bind=e)


def get_db() -> Generator[Session, None, None]:
    """Dependency provider yielding a managed transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
