"""Integration and authorization tests for Student Progress and History API (AdaptLearn M5).

Requirements Traceability:
- FR-21: GET /courses/{id}/progress endpoint.
- FR-15: GET /courses/{id}/attempts endpoint.
- NFR-05: Server-side access control.
- NFR-06: Privacy — student can only access own progress; instructor can access course students.
- NFR-04: Token-based authentication.
"""
import pytest
from fastapi.testclient import TestClient

from app.engine.recommendation_strategy import TopicRecommendationInput
from app.main import app
from app.repositories.adaptive_repository import get_adaptive_repository
from app.repositories.progress_repository import AttemptRecord, get_progress_repository


@pytest.fixture(autouse=True)
def reset_repos():
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


class TestStudentProgressEndpoint:
    """Validate GET /api/v1/courses/{id}/progress."""

    def test_get_progress_authorized_student(self, client):
        """Enrolled student accesses their own course progress -> 200 OK."""
        p_repo = get_progress_repository()
        a_repo = get_adaptive_repository()

        student_id = 10
        course_id = 100
        p_repo.enroll_student(student_id=student_id, course_id=course_id)
        a_repo.set_course_topics(
            course_id,
            [
                TopicRecommendationInput(topic_id=1, name="Variables", mastery_level="Proficient", score=0.90),
                TopicRecommendationInput(topic_id=2, name="Functions", mastery_level="Weak", score=0.35),
            ],
        )

        headers = {"Authorization": f"Bearer token-{student_id}-student"}
        response = client.get(f"/api/v1/courses/{course_id}/progress", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == student_id
        assert data["course_id"] == course_id
        assert data["completion_percentage"] == 50.0
        assert len(data["topic_breakdown"]) == 2
        # Recommendations included per FR-21
        assert "recommended_topics" in data
        assert len(data["recommended_topics"]) == 1
        assert data["recommended_topics"][0]["topic_name"] == "Functions"

    def test_get_progress_forbidden_non_enrolled_student(self, client):
        """Student not enrolled in the course -> 403 Forbidden."""
        student_id = 11
        course_id = 100
        # Student 11 is NOT enrolled in course 100

        headers = {"Authorization": f"Bearer token-{student_id}-student"}
        response = client.get(f"/api/v1/courses/{course_id}/progress", headers=headers)

        assert response.status_code == 403
        assert "not enrolled" in response.json()["error"]["message"].lower()

    def test_get_progress_forbidden_cross_student_access(self, client):
        """Student A cannot access Student B's progress -> 403 Forbidden (NFR-06)."""
        p_repo = get_progress_repository()
        student_a = 21
        student_b = 22
        course_id = 100
        p_repo.enroll_student(student_id=student_a, course_id=course_id)
        p_repo.enroll_student(student_id=student_b, course_id=course_id)

        # Student A requests Student B's progress
        headers = {"Authorization": f"Bearer token-{student_a}-student"}
        response = client.get(f"/api/v1/courses/{course_id}/progress?student_id={student_b}", headers=headers)

        assert response.status_code == 403
        assert "cannot access another student" in response.json()["error"]["message"].lower()

    def test_get_progress_instructor_can_access_student_progress(self, client):
        """Instructor who owns the course can access enrolled student's progress (NFR-06)."""
        p_repo = get_progress_repository()
        instructor_id = 99
        student_id = 30
        course_id = 105

        p_repo.set_course_owner(course_id=course_id, instructor_id=instructor_id)
        p_repo.enroll_student(student_id=student_id, course_id=course_id)

        headers = {"Authorization": f"Bearer token-{instructor_id}-instructor"}
        response = client.get(
            f"/api/v1/courses/{course_id}/progress?student_id={student_id}",
            headers=headers,
        )

        assert response.status_code == 200
        assert response.json()["student_id"] == student_id

    def test_get_progress_unauthenticated(self, client):
        """Request without Authorization header -> 401 Unauthorized (NFR-04)."""
        response = client.get("/api/v1/courses/100/progress")
        assert response.status_code == 401


class TestStudentAttemptHistoryEndpoint:
    """Validate GET /api/v1/courses/{id}/attempts."""

    def test_get_attempt_history_paginated(self, client):
        """Enrolled student views their paginated attempt history (FR-15)."""
        p_repo = get_progress_repository()
        student_id = 40
        course_id = 200
        p_repo.enroll_student(student_id=student_id, course_id=course_id)

        for i in range(1, 8):
            p_repo.record_attempt(
                AttemptRecord(
                    attempt_id=i,
                    student_id=student_id,
                    course_id=course_id,
                    quiz_id=1,
                    quiz_title="Quiz Basics",
                    score=0.8,
                    total_questions=5,
                    submitted_at="2026-11-21T00:00:00Z",
                )
            )

        headers = {"Authorization": f"Bearer token-{student_id}-student"}
        response = client.get(
            f"/api/v1/courses/{course_id}/attempts?page=1&page_size=5",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_attempts"] == 7
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["attempts"]) == 5
