"""Unit and integration regression tests for authentication token contract.

Requirements Traceability:
- NFR-04: Signed tokens / token-based session verification.
- NFR-05: Server-side access control for protected endpoints.
- DEF-AUTH-001: Token format contract alignment between frontend and backend.
"""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.auth import CurrentUser, get_current_user
from app.main import app
from app.repositories.adaptive_repository import get_adaptive_repository
from app.repositories.progress_repository import get_progress_repository


@pytest.fixture(autouse=True)
def reset_stores():
    """Reset repository stores between test runs."""
    p_repo = get_progress_repository()
    a_repo = get_adaptive_repository()
    p_repo.clear()
    a_repo.clear()
    yield
    p_repo.clear()
    a_repo.clear()


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Unit Tests for get_current_user
# ---------------------------------------------------------------------------


class TestGetCurrentUserContract:
    """Validate token contract parsing and rejection logic in get_current_user."""

    def test_student_preset_token_authenticates_successfully(self):
        """Student preset credential 'token-101-student' authenticates as student."""
        user = get_current_user(authorization="Bearer token-101-student")
        assert isinstance(user, CurrentUser)
        assert user.user_id == 101
        assert user.role == "student"

    def test_instructor_preset_token_authenticates_successfully(self):
        """Instructor preset credential 'token-1-instructor' authenticates as instructor."""
        user = get_current_user(authorization="Bearer token-1-instructor")
        assert isinstance(user, CurrentUser)
        assert user.user_id == 1
        assert user.role == "instructor"

    def test_non_owner_instructor_preset_token_authenticates_successfully(self):
        """Non-owner instructor preset credential 'token-2-instructor' authenticates."""
        user = get_current_user(authorization="Bearer token-2-instructor")
        assert isinstance(user, CurrentUser)
        assert user.user_id == 2
        assert user.role == "instructor"

    def test_token_parsing_case_insensitive_and_whitespace_tolerant(self):
        """Token parsing tolerates case variations and extra whitespace."""
        user = get_current_user(authorization="bearer   TOKEN-101-STUDENT  ")
        assert user.user_id == 101
        assert user.role == "student"

    def test_rejects_legacy_mismatch_format_dev_token(self):
        """Legacy format 'Bearer dev-token-student-101' is rejected with HTTP 401."""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(authorization="Bearer dev-token-student-101")
        assert exc_info.value.status_code == 401
        assert "Invalid authentication token format" in exc_info.value.detail

    def test_rejects_missing_authorization_header(self):
        """Missing Authorization header (None) raises HTTP 401."""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(authorization=None)
        assert exc_info.value.status_code == 401
        assert "missing Authorization header" in exc_info.value.detail

    def test_rejects_empty_authorization_header(self):
        """Empty string Authorization header raises HTTP 401."""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(authorization="")
        assert exc_info.value.status_code == 401

    @pytest.mark.parametrize(
        "malformed_header",
        [
            "Bearer invalid",
            "Bearer token-abc-student",
            "Bearer token-101-admin",
            "token-101-student",
            "Basic dXNlcjpwYXNz",
            "Bearer token--student",
            "Bearer token-101-",
        ],
    )
    def test_rejects_malformed_token_formats(self, malformed_header):
        """Various invalid schemes and formats raise HTTP 401."""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(authorization=malformed_header)
        assert exc_info.value.status_code == 401
        assert "Invalid authentication token format" in exc_info.value.detail


# ---------------------------------------------------------------------------
# Integration Tests against Protected API Endpoints
# ---------------------------------------------------------------------------


class TestProtectedApiAuthContract:
    """Validate that API endpoints enforce the token contract end-to-end."""

    def test_student_preset_token_succeeds_on_protected_progress_endpoint(self, client):
        """Enrolled student using preset token accesses progress endpoint -> 200 OK."""
        p_repo = get_progress_repository()
        p_repo.enroll_student(student_id=101, course_id=100)

        response = client.get(
            "/api/v1/courses/100/progress",
            headers={"Authorization": "Bearer token-101-student"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == 101
        assert data["course_id"] == 100

    def test_instructor_preset_token_succeeds_on_instructor_endpoint(self, client):
        """Instructor using preset token accesses course mastery distribution -> 200 OK."""
        p_repo = get_progress_repository()
        p_repo.set_course_owner(course_id=100, instructor_id=1)

        response = client.get(
            "/api/v1/courses/100/analytics/mastery-distribution",
            headers={"Authorization": "Bearer token-1-instructor"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["course_id"] == 100

    def test_legacy_dev_token_rejected_on_api_with_401(self, client):
        """Legacy 'dev-token-student-101' receives HTTP 401 on protected endpoint."""
        response = client.get(
            "/api/v1/courses/100/progress",
            headers={"Authorization": "Bearer dev-token-student-101"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "Invalid authentication token format" in data["error"]["message"]

    def test_unauthenticated_request_rejected_on_api_with_401(self, client):
        """Request without Authorization header receives HTTP 401."""
        response = client.get("/api/v1/courses/100/progress")
        assert response.status_code == 401
        data = response.json()
        assert "missing Authorization header" in data["error"]["message"]
