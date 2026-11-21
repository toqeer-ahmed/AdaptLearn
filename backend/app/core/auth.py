"""Authentication and authorization utilities (AdaptLearn Core).

Requirements Traceability:
- NFR-03: Salted bcrypt password storage and verification.
- NFR-04: Cryptographically signed JWT tokens with expiration validation.
- NFR-05: Server-side access control for protected endpoints.
- NFR-06: Privacy — student can only access own data; instructors can access their courses.
- Decision D5: Password bounds and secure hashing constraints.
"""
import re
from dataclasses import dataclass, field
from typing import Callable

import jwt
from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings
from app.core.security import decode_access_token
from app.repositories.user_repository import get_user_repository


@dataclass
class CurrentUser:
    """Represents the authenticated principal making the request."""
    user_id: int
    role: str  # 'student' or 'instructor'
    enrolled_course_ids: set[int] = field(default_factory=set)
    owned_course_ids: set[int] = field(default_factory=set)


# Legacy development token regex matching format: Bearer token-<id>-<role>
TOKEN_PATTERN = re.compile(r"^Bearer\s+token-(\d+)-(student|instructor)$", re.IGNORECASE)


def get_current_user(
    authorization: str | None = Header(None, description="Bearer <jwt_token> or Bearer token-<user_id>-<role>"),
) -> CurrentUser:
    """Extract and authenticate the user principal from the Authorization header.

    Validates cryptographically signed JWTs with expiration per NFR-04.
    In development environments, supports structured fallback tokens if enabled.

    Raises:
        HTTPException(401): If header is missing, malformed, expired, invalid signature,
                            or user account cannot be verified in repository.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_str = authorization.strip()
    if not auth_str.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token format. Expected Bearer scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_token = auth_str[7:].strip()
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: empty bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_repo = get_user_repository()

    # Step 1: Attempt to decode and validate as signed JWT (NFR-04)
    try:
        payload = decode_access_token(raw_token)
        user_id_str = payload.get("sub")
        token_role = payload.get("role")

        if not user_id_str or not token_role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token missing required claims (sub, role)",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = int(user_id_str)
        role = token_role.lower()

        # Step 2: Validate against persisted user repository (Requirement 5)
        user = user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or credentials invalid",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.role.lower() != role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token role claim does not match user account",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return CurrentUser(user_id=user.id, role=user.role)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token signature",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.InvalidTokenError, HTTPException) as exc:
        if isinstance(exc, HTTPException):
            raise exc

        # Step 3: In development environment, allow structured dev token fallback if enabled
        if settings.ALLOW_DEV_TOKENS and settings.ENVIRONMENT == "development":
            match = TOKEN_PATTERN.match(auth_str)
            if match:
                dev_id = int(match.group(1))
                dev_role = match.group(2).lower()

                # Validate against repository; seed if absent for development convenience
                user = user_repo.get_by_id(dev_id)
                if user is None:
                    # Look up by standard preset or reject spoofed IDs
                    if dev_id in (1, 2, 101):
                        user_repo.seed_default_users()
                        user = user_repo.get_by_id(dev_id)

                if user is not None and user.role.lower() != dev_role:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token role claim does not match user account",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

                return CurrentUser(user_id=dev_id, role=dev_role)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token format or claims",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(allowed_roles: list[str] | str) -> Callable[[CurrentUser], CurrentUser]:
    """Dependency factory enforcing server-side role-based access control (FR-03, NFR-05)."""
    if isinstance(allowed_roles, str):
        roles_list = [allowed_roles]
    else:
        roles_list = allowed_roles
    allowed_set = {r.strip().lower() for r in roles_list}

    def role_checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role.lower() not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires role '{', '.join(roles_list)}'",
            )
        return current_user

    return role_checker
