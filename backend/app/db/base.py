"""SQLAlchemy declarative base for AdaptLearn ORM entities."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all persistent domain models."""
    pass
