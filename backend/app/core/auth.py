"""Lightweight authentication and authorization utilities (AdaptLearn Core).

Requirements Traceability:
- NFR-04: Signed tokens / token-based session verification.
- NFR-05: Server-side access control for protected endpoints.
- NFR-06: Privacy — student can only access own data; instructors can access their courses.
"""
import re
from dataclasses import dataclass, field

from fastapi import Header, HTTPException, status


@dataclass
class CurrentUser:
    """Represents the authenticated principal making the request."""
    user_id: int
    role: str  # 'student' or 'instructor'
    enrolled_course_ids: set[int] = field(default_factory=set)
    owned_course_ids: set[int] = field(default_factory=set)


# Token parser regex matching format: Bearer token-<id>-<role>
TOKEN_PATTERN = re.compile(r"^Bearer\s+token-(\d+)-(student|instructor)$", re.IGNORECASE)


def get_current_user(
    authorization: str | None = Header(None, description="Bearer token-<user_id>-<role>"),
) -> CurrentUser:
    """Extract and authenticate the user principal from the Authorization header.

    In this phase, parses structured bearer tokens (token-<id>-<role>).
    In subsequent tasks, this verifies cryptographically signed JWTs per NFR-04.

    Raises:
        HTTPException(401): If the header is missing, malformed, or unauthenticated.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    match = TOKEN_PATTERN.match(authorization.strip())
    if not match:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token format. Expected: Bearer token-<id>-<role>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = int(match.group(1))
    role = match.group(2).lower()

    return CurrentUser(user_id=user_id, role=role)
