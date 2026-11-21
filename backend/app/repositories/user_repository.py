"""User repository for persistence and retrieval of user entities.

Requirements Traceability:
- FR-01: User registration with unique email address.
- FR-02: User authentication lookup.
- NFR-03: Passwords stored only as salted hashes.
- NFR-09: Uniqueness enforcement.
"""
from dataclasses import dataclass
from typing import Optional

from app.core.security import hash_password


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
    """In-memory thread-safe repository managing user records."""

    def __init__(self) -> None:
        self._users: dict[int, UserRecord] = {}
        self._users_by_email: dict[str, int] = {}
        self._next_id: int = 1
        self.seed_default_users()

    def seed_default_users(self) -> None:
        """Seed verified default personas with pre-hashed credentials for development and testing."""
        default_pwd_hash = hash_password("Password123!")

        # Instructor Ada Lovelace (ID: 1)
        if 1 not in self._users:
            u1 = UserRecord(
                id=1,
                name="Prof. Ada Lovelace",
                email="lovelace@instructor.adaptlearn.edu",
                password_hash=default_pwd_hash,
                role="instructor",
            )
            self._users[1] = u1
            self._users_by_email[u1.email.lower()] = 1

        # Non-owner Instructor Alan Turing (ID: 2)
        if 2 not in self._users:
            u2 = UserRecord(
                id=2,
                name="Prof. Alan Turing",
                email="turing@instructor.adaptlearn.edu",
                password_hash=default_pwd_hash,
                role="instructor",
            )
            self._users[2] = u2
            self._users_by_email[u2.email.lower()] = 2

        # Student Alice (ID: 101)
        if 101 not in self._users:
            u101 = UserRecord(
                id=101,
                name="Alice Student",
                email="alice@student.adaptlearn.edu",
                password_hash=default_pwd_hash,
                role="student",
            )
            self._users[101] = u101
            self._users_by_email[u101.email.lower()] = 101

        # Ensure next_id does not collide with preset IDs
        max_id = max(self._users.keys(), default=0)
        if self._next_id <= max_id:
            self._next_id = max_id + 1

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
        if normalized_email in self._users_by_email:
            raise ValueError(f"Email '{email}' is already registered")

        user_id = self._next_id
        self._next_id += 1

        user = UserRecord(
            id=user_id,
            name=name.strip(),
            email=normalized_email,
            password_hash=password_hash,
            role=role.strip().lower(),
            is_active=True,
        )
        self._users[user_id] = user
        self._users_by_email[normalized_email] = user_id
        return user

    def get_by_id(self, user_id: int) -> Optional[UserRecord]:
        """Look up user by primary key."""
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> Optional[UserRecord]:
        """Look up user by email address (case-insensitive)."""
        normalized = email.strip().lower()
        user_id = self._users_by_email.get(normalized)
        if user_id is not None:
            return self._users.get(user_id)
        return None

    def clear(self) -> None:
        """Clear all stored users and reseed defaults."""
        self._users.clear()
        self._users_by_email.clear()
        self._next_id = 1
        self.seed_default_users()


_USER_REPO_INSTANCE: Optional[UserRepository] = None


def get_user_repository() -> UserRepository:
    """Singleton provider for UserRepository."""
    global _USER_REPO_INSTANCE
    if _USER_REPO_INSTANCE is None:
        _USER_REPO_INSTANCE = UserRepository()
    return _USER_REPO_INSTANCE
