"""SQLAlchemy ORM model for user authentication records."""
from sqlalchemy import Boolean, Column, Integer, String

from app.db.base import Base


class UserModel(Base):
    """User account entity (FR-01, FR-02, NFR-03)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(254), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
