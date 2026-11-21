"""Pydantic schemas for user registration, authentication, and JWT tokens.

Requirements Traceability:
- FR-01: User registration with name, email, password, role.
- FR-02: User login and token generation.
- NFR-03: Passwords never logged or returned in responses.
- Decision D5: Input bounds (name 1-100, email <= 254, password 8-72).
"""
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRegisterRequest(BaseModel):
    """Payload for user registration (FR-01, Decision D5)."""
    name: str = Field(..., min_length=1, max_length=100, description="Full name (1-100 characters)")
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=254, description="Unique email address (max 254 characters)")
    password: str = Field(..., min_length=8, max_length=72, description="Password (8-72 characters per bcrypt)")
    role: str = Field(..., pattern=r"^(?i)(student|instructor)$", description="User role ('Student' or 'Instructor')")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Name cannot be empty or whitespace only")
        return stripped

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        return v.strip().lower()

    model_config = ConfigDict(str_strip_whitespace=True)


class UserLoginRequest(BaseModel):
    """Payload for user login (FR-02)."""
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., description="User password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    """Public user profile response (NFR-03: excludes password_hash)."""
    id: int
    name: str
    email: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Bearer token response upon successful login (NFR-04)."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
