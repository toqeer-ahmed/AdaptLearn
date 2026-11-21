"""Authentication and user management business logic service.

Requirements Traceability:
- FR-01: User registration logic and duplicate email rejection.
- FR-02: User login and authenticated session token issuance.
- NFR-03: Salted bcrypt password hashing.
- NFR-04: Signed JWT issuance with 60-minute expiration.
- NFR-05: Server-side access control.
- AGENTS.md Rule 2: Service calls Repository and Core Security only.
"""

from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import (
    UserRecord,
    UserRepository,
    get_user_repository,
)
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)


class AuthService:
    """Service handling user registration, authentication, and token generation."""

    def __init__(self, user_repo: UserRepository | None = None) -> None:
        self.user_repo = user_repo or get_user_repository()

    def register(self, payload: UserRegisterRequest) -> UserResponse:
        """Register a new student or instructor account.

        Raises:
            HTTPException(409): If email address is already registered.
            HTTPException(400): If validation rules are violated.
        """
        existing = self.user_repo.get_by_email(payload.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email address '{payload.email}' is already registered",
            )

        password_hash = hash_password(payload.password)
        user = self.user_repo.create_user(
            name=payload.name,
            email=payload.email,
            password_hash=password_hash,
            role=payload.role,
        )

        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
        )

    def login(self, payload: UserLoginRequest) -> TokenResponse:
        """Authenticate user credentials and issue signed JWT access token.

        Raises:
            HTTPException(401): For non-existent email or invalid password
                                (identical generic message to prevent enumeration).
        """
        user = self.user_repo.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated",
            )

        token_data = {
            "sub": str(user.id),
            "role": user.role,
            "email": user.email,
        }
        access_token = create_access_token(data=token_data)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
            ),
        )

    def get_user_by_id(self, user_id: int) -> UserRecord | None:
        """Fetch user by primary key."""
        return self.user_repo.get_by_id(user_id)


_AUTH_SERVICE_INSTANCE: AuthService | None = None


def get_auth_service() -> AuthService:
    """Singleton provider for AuthService."""
    global _AUTH_SERVICE_INSTANCE
    if _AUTH_SERVICE_INSTANCE is None:
        _AUTH_SERVICE_INSTANCE = AuthService()
    return _AUTH_SERVICE_INSTANCE
