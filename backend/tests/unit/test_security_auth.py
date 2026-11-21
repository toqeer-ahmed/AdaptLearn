"""Comprehensive regression and security test suite for authentication and cryptography.

Requirements Traceability:
- FR-01: User registration with name, email, password, role.
- FR-02: User login with JWT session token issuance.
- FR-03: Server-side role-based access control.
- NFR-03: Passwords stored only as salted bcrypt hashes, never returned in responses.
- NFR-04: Cryptographically signed JWT tokens with expiration validation.
- NFR-05: Server-side access control.
- Decision D5: Password bounds 8-72 characters (bcrypt limit).
- SQA DEF-AUTH-002: Cryptographic signing and expiry validation.
- SQA DEF-AUTH-003: Backend registration, login, and password hashing endpoints.
"""
from datetime import timedelta
import time

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.main import app
from app.repositories.progress_repository import get_progress_repository
from app.repositories.user_repository import get_user_repository
from app.schemas.auth import UserLoginRequest, UserRegisterRequest
from app.services.auth_service import get_auth_service


@pytest.fixture(autouse=True)
def reset_stores():
    """Reset user and progress repository singletons between tests."""
    u_repo = get_user_repository()
    p_repo = get_progress_repository()
    u_repo.clear()
    p_repo.clear()
    yield
    u_repo.clear()
    p_repo.clear()


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Password Hashing & Bcrypt Verification (NFR-03, Decision D5)
# ---------------------------------------------------------------------------


class TestPasswordHashingAndBcrypt:
    """Validate bcrypt password hashing, salting, bounds, and exposure prevention."""

    def test_hash_password_produces_salted_bcrypt_hash(self):
        """Hashes use bcrypt format ($2b$), 12 rounds, and generate unique salts."""
        raw_pwd = "MySecretPassword123!"
        hash1 = hash_password(raw_pwd)
        hash2 = hash_password(raw_pwd)

        assert hash1.startswith("$2b$12$")
        assert hash2.startswith("$2b$12$")
        # Different salts mean hashes must not be identical
        assert hash1 != hash2

    def test_verify_password_verifies_correct_and_rejects_incorrect(self):
        """verify_password returns True for matching plaintext, False otherwise."""
        raw_pwd = "CorrectHorseBatteryStaple"
        pwd_hash = hash_password(raw_pwd)

        assert verify_password(raw_pwd, pwd_hash) is True
        assert verify_password("WrongPassword123", pwd_hash) is False
        assert verify_password("", pwd_hash) is False
        assert verify_password(raw_pwd, "not-a-valid-hash") is False

    def test_password_length_bounds_enforced(self):
        """Passwords cannot exceed 72 bytes (bcrypt truncation boundary, Decision D5)."""
        valid_pwd = "a" * 72
        assert hash_password(valid_pwd) is not None

        too_long_pwd = "a" * 73
        with pytest.raises(ValueError, match="cannot exceed 72 bytes"):
            hash_password(too_long_pwd)


# ---------------------------------------------------------------------------
# 2. JWT Cryptographic Token Primitives (NFR-04)
# ---------------------------------------------------------------------------


class TestJwtCryptographicPrimitives:
    """Validate signed token issuance, expiration, claim validation, and signature security."""

    def test_create_and_decode_valid_access_token(self):
        """Signed JWT encodes required claims (sub, role, iat, exp) and decodes cleanly."""
        payload = {"sub": "42", "role": "student", "email": "student42@adaptlearn.edu"}
        token = create_access_token(data=payload)

        decoded = decode_access_token(token)
        assert decoded["sub"] == "42"
        assert decoded["role"] == "student"
        assert decoded["email"] == "student42@adaptlearn.edu"
        assert "exp" in decoded
        assert "iat" in decoded
        assert decoded["exp"] > decoded["iat"]

    def test_decode_token_rejects_invalid_signature(self):
        """Tokens signed with a different key are rejected with InvalidSignatureError."""
        payload = {"sub": "42", "role": "student"}
        tampered_secret = "attacker-secret-key-that-is-at-least-32-chars-long"
        forged_token = create_access_token(data=payload, secret_key=tampered_secret)

        with pytest.raises(jwt.InvalidSignatureError):
            decode_access_token(forged_token)

    def test_decode_token_rejects_expired_token(self):
        """Tokens past expiration time are rejected with ExpiredSignatureError."""
        payload = {"sub": "42", "role": "student"}
        expired_token = create_access_token(data=payload, expires_delta=timedelta(seconds=-10))

        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(expired_token)

    def test_decode_token_rejects_missing_required_claims(self):
        """Tokens missing 'sub', 'role', or 'exp' claims are rejected."""
        # Token missing 'role'
        bad_payload = {"sub": "42", "exp": int(time.time()) + 3600, "iat": int(time.time())}
        token_no_role = jwt.encode(bad_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        with pytest.raises(jwt.InvalidTokenError):
            decode_access_token(token_no_role)

    def test_decode_token_rejects_malformed_string(self):
        """Malformed, non-JWT token strings raise InvalidTokenError."""
        with pytest.raises(jwt.InvalidTokenError):
            decode_access_token("this.is.not.a.valid.jwt")


# ---------------------------------------------------------------------------
# 3. User Registration Endpoint (FR-01, NFR-03, Decision D5)
# ---------------------------------------------------------------------------


class TestUserRegistrationApi:
    """Validate POST /api/v1/auth/register endpoint."""

    def test_register_student_success(self, client):
        """New student registers successfully -> 201 Created; password hash is excluded."""
        payload = {
            "name": "Jane Student",
            "email": "jane.student@adaptlearn.edu",
            "password": "StrongPassword2026!",
            "role": "Student",
        }
        res = client.post("/api/v1/auth/register", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Jane Student"
        assert data["email"] == "jane.student@adaptlearn.edu"
        assert data["role"] == "student"
        assert "password" not in data
        assert "password_hash" not in data

        # Verify password is salted in repository
        u_repo = get_user_repository()
        saved_user = u_repo.get_by_email("jane.student@adaptlearn.edu")
        assert saved_user is not None
        assert saved_user.password_hash.startswith("$2b$12$")
        assert verify_password("StrongPassword2026!", saved_user.password_hash) is True

    def test_register_instructor_success(self, client):
        """New instructor registers successfully -> 201 Created."""
        payload = {
            "name": "Dr. Grace Hopper",
            "email": "hopper@instructor.adaptlearn.edu",
            "password": "CompilerQueen1952!",
            "role": "Instructor",
        }
        res = client.post("/api/v1/auth/register", json=payload)
        assert res.status_code == 201
        assert res.json()["role"] == "instructor"

    def test_register_duplicate_email_rejected_with_409(self, client):
        """Duplicate email registration raises HTTP 409 Conflict."""
        payload = {
            "name": "Duplicate User",
            "email": "alice@student.adaptlearn.edu",  # Seeded default email
            "password": "Password123!",
            "role": "Student",
        }
        res = client.post("/api/v1/auth/register", json=payload)
        assert res.status_code == 409
        data = res.json()
        assert "already registered" in data["error"]["message"]

    @pytest.mark.parametrize(
        "invalid_payload,expected_err",
        [
            ({"name": "", "email": "a@b.com", "password": "Password123!", "role": "student"}, "empty"),
            ({"name": "A" * 101, "email": "a@b.com", "password": "Password123!", "role": "student"}, "characters"),
            ({"name": "Bob", "email": "not-an-email", "password": "Password123!", "role": "student"}, "Invalid email format"),
            ({"name": "Bob", "email": "bob@b.com", "password": "short", "role": "student"}, "at least 8 characters"),
            ({"name": "Bob", "email": "bob@b.com", "password": "P" * 73, "role": "student"}, "at most 72 characters"),
            ({"name": "Bob", "email": "bob@b.com", "password": "Password123!", "role": "admin"}, "student"),
        ],
    )
    def test_register_validation_errors(self, client, invalid_payload, expected_err):
        """Invalid fields are rejected by Pydantic schema validation with HTTP 422."""
        res = client.post("/api/v1/auth/register", json=invalid_payload)
        assert res.status_code == 422


# ---------------------------------------------------------------------------
# 4. User Login & Token Generation (FR-02, NFR-03, NFR-04)
# ---------------------------------------------------------------------------


class TestUserLoginApi:
    """Validate POST /api/v1/auth/login endpoint."""

    def test_login_success_returns_jwt_and_user_profile(self, client):
        """Correct email and password returns signed JWT access token and user info."""
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "alice@student.adaptlearn.edu", "password": "Password123!"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["id"] == 101
        assert data["user"]["role"] == "student"

        # Verify access token is valid JWT
        decoded = decode_access_token(data["access_token"])
        assert decoded["sub"] == "101"
        assert decoded["role"] == "student"

    def test_login_invalid_password_returns_401(self, client):
        """Incorrect password returns HTTP 401 with generic message (no enumeration)."""
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "alice@student.adaptlearn.edu", "password": "WrongPassword!"},
        )
        assert res.status_code == 401
        data = res.json()
        assert data["error"]["message"] == "Invalid email or password"

    def test_login_nonexistent_email_returns_401(self, client):
        """Unknown email returns identical generic 401 error message."""
        res = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@adaptlearn.edu", "password": "Password123!"},
        )
        assert res.status_code == 401
        data = res.json()
        assert data["error"]["message"] == "Invalid email or password"


# ---------------------------------------------------------------------------
# 5. Security & Authorization Enforcement (NFR-04, NFR-05, NFR-06)
# ---------------------------------------------------------------------------


class TestAuthenticationAndAuthorizationEnforcement:
    """Validate server-side protection, spoofing prevention, and role restrictions."""

    def test_authenticated_user_accesses_me_profile(self, client):
        """User accessing /api/v1/auth/me with valid JWT receives profile."""
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": "alice@student.adaptlearn.edu", "password": "Password123!"},
        )
        token = login_res.json()["access_token"]

        me_res = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        assert me_res.json()["id"] == 101
        assert me_res.json()["role"] == "student"

    def test_protected_endpoint_rejects_expired_jwt_with_401(self, client):
        """Expired JWT token is rejected with HTTP 401."""
        expired_jwt = create_access_token(
            data={"sub": "101", "role": "student"},
            expires_delta=timedelta(seconds=-10),
        )
        res = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_jwt}"},
        )
        assert res.status_code == 401
        assert "expired" in res.json()["error"]["message"]

    def test_protected_endpoint_rejects_invalid_signature_jwt_with_401(self, client):
        """JWT signed with unauthorized secret key is rejected with HTTP 401."""
        fake_jwt = create_access_token(
            data={"sub": "101", "role": "student"},
            secret_key="unauthorized-secret-key-that-is-at-least-32-chars",
        )
        res = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {fake_jwt}"},
        )
        assert res.status_code == 401
        assert "signature" in res.json()["error"]["message"]

    def test_user_identity_spoofing_rejected_with_401(self, client):
        """Attacker crafting token with non-existent user ID is rejected."""
        spoofed_jwt = create_access_token(
            data={"sub": "9999", "role": "student"},
        )
        res = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {spoofed_jwt}"},
        )
        assert res.status_code == 401
        assert "User account not found" in res.json()["error"]["message"]

    def test_role_spoofing_claim_tampering_rejected_with_401(self, client):
        """Student with modified role='instructor' in token is rejected against user record."""
        # Alice is student (ID: 101). Forging role='instructor' in token:
        spoofed_role_jwt = create_access_token(
            data={"sub": "101", "role": "instructor"},
        )
        res = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {spoofed_role_jwt}"},
        )
        assert res.status_code == 401
        assert "Token role claim does not match user account" in res.json()["error"]["message"]

    def test_student_token_forbidden_on_instructor_endpoint(self, client):
        """Student JWT attempting to view instructor analytics receives HTTP 403 Forbidden."""
        p_repo = get_progress_repository()
        p_repo.set_course_owner(course_id=100, instructor_id=1)

        student_jwt = create_access_token(data={"sub": "101", "role": "student"})
        res = client.get(
            "/api/v1/courses/100/analytics/mastery-distribution",
            headers={"Authorization": f"Bearer {student_jwt}"},
        )
        assert res.status_code == 403
        assert "instructor" in res.json()["error"]["message"]

    def test_instructor_token_succeeds_on_instructor_endpoint(self, client):
        """Instructor JWT accessing owned course analytics receives HTTP 200 OK."""
        p_repo = get_progress_repository()
        p_repo.set_course_owner(course_id=100, instructor_id=1)

        instructor_jwt = create_access_token(data={"sub": "1", "role": "instructor"})
        res = client.get(
            "/api/v1/courses/100/analytics/mastery-distribution",
            headers={"Authorization": f"Bearer {instructor_jwt}"},
        )
        assert res.status_code == 200
        assert res.json()["course_id"] == 100


# ---------------------------------------------------------------------------
# 6. Secret & Configuration Behavior (Requirement 8, 9, 10)
# ---------------------------------------------------------------------------


class TestConfigurationAndProductionIsolation:
    """Validate environment configuration isolation and legacy token bypass prevention."""

    def test_production_mode_strictly_rejects_legacy_tokens(self, client, monkeypatch):
        """In production (ALLOW_DEV_TOKENS=False), legacy 'token-101-student' raises 401."""
        monkeypatch.setattr(settings, "ALLOW_DEV_TOKENS", False)

        res = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer token-101-student"},
        )
        assert res.status_code == 401
        assert "Invalid authentication token format" in res.json()["error"]["message"]

    def test_development_mode_permits_legacy_tokens_for_existing_personas(self, client, monkeypatch):
        """In development (ALLOW_DEV_TOKENS=True), legacy token resolves to seeded persona."""
        monkeypatch.setattr(settings, "ALLOW_DEV_TOKENS", True)
        monkeypatch.setattr(settings, "ENVIRONMENT", "development")

        res = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer token-101-student"},
        )
        assert res.status_code == 200
        assert res.json()["id"] == 101

    def test_missing_authorization_header_rejected_with_401(self, client):
        """Missing Authorization header on protected endpoint raises 401."""
        res = client.get("/api/v1/auth/me")
        assert res.status_code == 401
        assert "missing Authorization header" in res.json()["error"]["message"]
