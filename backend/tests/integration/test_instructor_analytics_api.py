"""Integration and access control tests for Instructor Analytics API (AdaptLearn M5).

Requirements Traceability:
- FR-22: GET /courses/{id}/analytics/student-roster.
- FR-23: GET /courses/{id}/analytics/mastery-distribution.
- FR-24: GET /courses/{id}/analytics/questions.
- FR-03 & TC-03-1: Student calling instructor endpoint is rejected (403 Forbidden).
- TC-22-2: Instructor calling another instructor's course is rejected (403 Forbidden).
- NFR-04: Unauthenticated requests rejected (401 Unauthorized).
"""
import pytest
from fastapi.testclient import TestClient

from app.engine.recommendation_strategy import TopicRecommendationInput
from app.main import app
from app.repositories.adaptive_repository import get_adaptive_repository
from app.repositories.progress_repository import get_progress_repository


@pytest.fixture(autouse=True)
def reset_repos():
    """Reset repository stores between tests."""
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


class TestInstructorAnalyticsEndpoints:
    """Validate instructor analytics endpoints for course owners."""

    def test_get_mastery_distribution_authorized_instructor(self, client):
        """Instructor views topic mastery distribution for their course (FR-23)."""
        p_repo = get_progress_repository()
        a_repo = get_adaptive_repository()

        instructor_id = 1
        course_id = 700
        p_repo.set_course_owner(course_id=course_id, instructor_id=instructor_id)
        p_repo.enroll_student(10, course_id)
        a_repo.set_course_topics(
            course_id,
            [TopicRecommendationInput(topic_id=1, name="Topic 1", mastery_level="Not Assessed", score=0.0)],
        )

        headers = {"Authorization": f"Bearer token-{instructor_id}-instructor"}
        response = client.get(f"/api/v1/courses/{course_id}/analytics/mastery-distribution", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["course_id"] == course_id
        assert data["total_enrolled"] == 1
        assert len(data["topics"]) == 1

    def test_get_student_roster_authorized_instructor(self, client):
        """Instructor views student roster matrix for their course (FR-22)."""
        p_repo = get_progress_repository()
        a_repo = get_adaptive_repository()

        instructor_id = 1
        course_id = 701
        p_repo.set_course_owner(course_id=course_id, instructor_id=instructor_id)
        p_repo.enroll_student(10, course_id)
        a_repo.set_course_topics(
            course_id,
            [TopicRecommendationInput(topic_id=1, name="Topic 1", mastery_level="Not Assessed", score=0.0)],
        )

        headers = {"Authorization": f"Bearer token-{instructor_id}-instructor"}
        response = client.get(f"/api/v1/courses/{course_id}/analytics/student-roster", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["course_id"] == course_id
        assert len(data["students"]) == 1

    def test_get_question_stats_authorized_instructor(self, client):
        """Instructor views question statistics for their course (FR-24)."""
        p_repo = get_progress_repository()

        instructor_id = 1
        course_id = 702
        p_repo.set_course_owner(course_id=course_id, instructor_id=instructor_id)
        p_repo.add_course_question(
            course_id=course_id,
            question_id=55,
            question_text="Sample Question",
            topic_id=1,
            topic_name="T1",
            difficulty="Easy",
        )

        headers = {"Authorization": f"Bearer token-{instructor_id}-instructor"}
        response = client.get(f"/api/v1/courses/{course_id}/analytics/questions", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["course_id"] == course_id
        assert len(data["questions"]) == 1


class TestInstructorAccessControl:
    """Validate server-side access control (FR-03, TC-03-1, TC-22-2, NFR-05)."""

    def test_student_calling_instructor_endpoint_rejected_tc_03_1(self, client):
        """TC-03-1: A student calling an instructor endpoint is rejected (403 Forbidden)."""
        p_repo = get_progress_repository()
        course_id = 800
        p_repo.set_course_owner(course_id=course_id, instructor_id=1)
        p_repo.enroll_student(student_id=5, course_id=course_id)

        headers = {"Authorization": "Bearer token-5-student"}
        response = client.get(f"/api/v1/courses/{course_id}/analytics/mastery-distribution", headers=headers)

        assert response.status_code == 403
        assert "cannot call instructor endpoints" in response.json()["error"]["message"].lower()

    def test_wrong_instructor_calling_course_rejected_tc_22_2(self, client):
        """TC-22-2: An instructor requests progress of another instructor's course -> 403 Forbidden."""
        p_repo = get_progress_repository()
        course_id = 801
        # Course 801 is owned by Instructor 1
        p_repo.set_course_owner(course_id=course_id, instructor_id=1)

        # Instructor 2 attempts access
        headers = {"Authorization": "Bearer token-2-instructor"}
        response = client.get(f"/api/v1/courses/{course_id}/analytics/student-roster", headers=headers)

        assert response.status_code == 403
        assert "does not own this course" in response.json()["error"]["message"].lower()

    def test_unauthenticated_request_rejected(self, client):
        """Request without Authorization header -> 401 Unauthorized (NFR-04)."""
        response = client.get("/api/v1/courses/800/analytics/questions")
        assert response.status_code == 401
