"""Security and cryptographic primitives for AdaptLearn (Core).

Requirements Traceability:
- NFR-03: Passwords stored only as salted hashes (bcrypt). Never logged or returned.
- NFR-04: Signed tokens with expiry time. Requests with missing/invalid/expired tokens rejected.
- NFR-05: Server-side access control.
- Decision D5: Password length 8-72 characters (bcrypt 72-byte limit).
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with automatic salt generation."""
    pwd_bytes = password.encode("utf-8")
    if len(pwd_bytes) > 72:
        raise ValueError("Password cannot exceed 72 bytes per bcrypt standard (Decision D5)")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
    secret_key: str | None = None,
    algorithm: str | None = None,
) -> str:
    """Create a cryptographically signed JWT access token with standard claims.

    Required data payload keys:
    - sub: stringified user ID
    - role: user role ('student' or 'instructor')
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    })

    key = secret_key or settings.JWT_SECRET_KEY
    alg = algorithm or settings.JWT_ALGORITHM

    return jwt.encode(to_encode, key, algorithm=alg)


def decode_access_token(
    token: str,
    secret_key: str | None = None,
    algorithm: str | None = None,
) -> dict[str, Any]:
    """Decode and validate a signed JWT token.

    Validates signature, expiration, and presence of required claims ('sub', 'role').

    Raises:
        jwt.ExpiredSignatureError: If token has expired.
        jwt.InvalidSignatureError: If token signature does not match secret key.
        jwt.InvalidTokenError: If token is malformed, missing claims, or invalid.
    """
    key = secret_key or settings.JWT_SECRET_KEY
    alg = algorithm or settings.JWT_ALGORITHM

    payload = jwt.decode(
        token,
        key,
        algorithms=[alg],
        options={"require": ["sub", "role", "exp", "iat"]},
    )
    return payload
