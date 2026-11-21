"""User repository for persistence and retrieval of user entities.

Requirements Traceability:
- FR-01: User registration with unique email address.
- FR-02: User authentication lookup.
- NFR-03: Passwords stored only as salted hashes.
- NFR-09: Uniqueness enforcement.
- NFR-07 & NFR-08: Persistent database storage.
"""
from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import hash_password
from app.db.session import SessionLocal, init_db
from app.models.user import UserModel


@dataclass
class UserRecord:
    """Represents a persisted user account."""
    id: int
    name: str
    email: str
    password_hash: str
    role: str  # 'student' or 'instructor'
    is_active: bool = True


class UserRepository:
    """SQLAlchemy persistent repository managing user records."""

    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self.session_factory = session_factory or SessionLocal
        init_db()
        self.seed_default_users()

    def seed_default_users(self) -> None:
        """Seed verified default personas with pre-hashed credentials for development and testing."""
        default_pwd_hash = hash_password("Password123!")

        with self.session_factory() as session:
            # Instructor Ada Lovelace (ID: 1)
            if not session.query(UserModel).filter_by(id=1).first():
                session.add(
                    UserModel(
                        id=1,
                        name="Prof. Ada Lovelace",
                        email="lovelace@instructor.adaptlearn.edu",
                        password_hash=default_pwd_hash,
                        role="instructor",
                        is_active=True,
                    )
                )

            # Non-owner Instructor Alan Turing (ID: 2)
            if not session.query(UserModel).filter_by(id=2).first():
                session.add(
                    UserModel(
                        id=2,
                        name="Prof. Alan Turing",
                        email="turing@instructor.adaptlearn.edu",
                        password_hash=default_pwd_hash,
                        role="instructor",
                        is_active=True,
                    )
                )

            # Student Alice (ID: 101)
            if not session.query(UserModel).filter_by(id=101).first():
                session.add(
                    UserModel(
                        id=101,
                        name="Alice Student",
                        email="alice@student.adaptlearn.edu",
                        password_hash=default_pwd_hash,
                        role="student",
                        is_active=True,
                    )
                )

            session.commit()

    def create_user(
        self,
        name: str,
        email: str,
        password_hash: str,
        role: str,
    ) -> UserRecord:
        """Persist a new user record.

        Raises:
            ValueError: If email is already registered.
        """
        normalized_email = email.strip().lower()

        with self.session_factory() as session:
            existing = session.query(UserModel).filter_by(email=normalized_email).first()
            if existing is not None:
                raise ValueError(f"Email '{email}' is already registered")

            max_id = session.query(func.max(UserModel.id)).scalar() or 0
            next_id = max(max_id + 1, 102) if max_id >= 101 else max_id + 1

            user = UserModel(
                id=next_id,
                name=name.strip(),
                email=normalized_email,
                password_hash=password_hash,
                role=role.strip().lower(),
                is_active=True,
            )
            session.add(user)
            session.commit()

            return UserRecord(
                id=user.id,
                name=user.name,
                email=user.email,
                password_hash=user.password_hash,
                role=user.role,
                is_active=user.is_active,
            )

    def get_by_id(self, user_id: int) -> UserRecord | None:
        """Look up user by primary key."""
        with self.session_factory() as session:
            u = session.query(UserModel).filter_by(id=user_id).first()
            if u:
                return UserRecord(
                    id=u.id,
                    name=u.name,
                    email=u.email,
                    password_hash=u.password_hash,
                    role=u.role,
                    is_active=u.is_active,
                )
            return None

    def get_by_email(self, email: str) -> UserRecord | None:
        """Look up user by email address (case-insensitive)."""
        normalized = email.strip().lower()
        with self.session_factory() as session:
            u = session.query(UserModel).filter_by(email=normalized).first()
            if u:
                return UserRecord(
                    id=u.id,
                    name=u.name,
                    email=u.email,
                    password_hash=u.password_hash,
                    role=u.role,
                    is_active=u.is_active,
                )
            return None

    def clear(self) -> None:
        """Clear all stored users and reseed defaults."""
        with self.session_factory() as session:
            session.query(UserModel).delete()
            session.commit()
        self.seed_default_users()


_USER_REPO_INSTANCE: UserRepository | None = None


def get_user_repository() -> UserRepository:
    """Singleton provider for UserRepository."""
    global _USER_REPO_INSTANCE
    if _USER_REPO_INSTANCE is None:
        _USER_REPO_INSTANCE = UserRepository()
    return _USER_REPO_INSTANCE
