"""Authentication endpoints (Module 1: User & Course Management).

Requirements Traceability:
- FR-01: POST /api/v1/auth/register (user registration).
- FR-02: POST /api/v1/auth/login (user login with JWT issuance).
- NFR-03: Passwords stored only as salted bcrypt hashes.
- NFR-04: Signed JWT tokens with expiry.
- NFR-05: Server-side access control.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.auth import CurrentUser, get_current_user
from app.schemas.auth import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService, get_auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account (FR-01)",
)
def register(
    payload: UserRegisterRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Register a new student or instructor with unique email and bcrypt password."""
    return service.register(payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive a signed JWT token (FR-02, NFR-04)",
)
def login(
    payload: UserLoginRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Authenticate with email and password, returning signed JWT access token."""
    return service.login(payload)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
def get_current_user_profile(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    """Return identity and role of the currently authenticated principal."""
    user = service.get_user_by_id(current_user.user_id)
    if not user:
        return UserResponse(
            id=current_user.user_id,
            name=f"User {current_user.user_id}",
            email=f"user{current_user.user_id}@adaptlearn.edu",
            role=current_user.role,
        )
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
    )
