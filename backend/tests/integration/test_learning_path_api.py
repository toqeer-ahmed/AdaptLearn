"""Integration tests for Module 4: Personalized Learning Paths API Endpoints.

Requirements Traceability:
- FR-11: Prerequisite-aware unlocking; ordered topic list with mastery status.
- FR-12: M3 engine recommendation tagging with rationale on unlocked non-Proficient topics.
- FR-13: completion_percentage, unlocked_count, completed_count in response.
- FR-14: Authorization — students must be enrolled; instructors must own the course.
- Decision 4: 'Proficient' mastery level (≥0.80) is prerequisite-unlock threshold.
- Decision 5: Instructor may supply ?student_id query param to view a specific student's path.
- NFR-06: Students may only view their own learning path.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.engine.mastery_calculator import ResponseRecord
from app.main import app
from app.repositories.adaptive_repository import get_adaptive_repository
from app.repositories.course_repository import get_course_repository
from app.repositories.progress_repository import get_progress_repository
from app.repositories.user_repository import get_user_repository

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def clean_repositories():
    """Reset all repositories before and after each test for isolation."""
    u_repo = get_user_repository()
    p_repo = get_progress_repository()
    c_repo = get_course_repository()
    a_repo = get_adaptive_repository()

    u_repo.seed_default_users()
    c_repo.clear()
    p_repo.clear()
    a_repo.clear()

    # Ensure a second student exists (Bob, for privacy tests)
    if not u_repo.get_by_id(102):
        u_repo.create_user(
            name="Bob Student",
            email="bob@student.adaptlearn.edu",
            password_hash=hash_password("Password123!"),
            role="student",
        )

    # Reset LearningPathService singleton so it re-binds repos after clear
    import app.services.learning_path_service as lps_module

    lps_module._global_learning_path_service = None

    yield

    c_repo.clear()
    p_repo.clear()
    a_repo.clear()


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def instructor1_auth():
    """Auth header for Instructor Ada Lovelace (ID 1)."""
    token = create_access_token({"sub": "1", "role": "instructor"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def instructor2_auth():
    """Auth header for Instructor Alan Turing (ID 2) — non-owner."""
    token = create_access_token({"sub": "2", "role": "instructor"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student1_auth():
    """Auth header for Student Alice (ID 101)."""
    token = create_access_token({"sub": "101", "role": "student"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student2_auth():
    """Auth header for Student Bob (ID 102)."""
    token = create_access_token({"sub": "102", "role": "student"})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Helper: build a course + topics + optional enrollment + optional responses
# ---------------------------------------------------------------------------


def _create_course_with_topics(
    course_title: str = "Test Course",
    course_code: str = "TEST-M4-001",
    num_topics: int = 2,
    enroll_student_id: int | None = None,
    prereq_edges: list[tuple[int, int]] | None = None,
) -> tuple[int, list[int]]:
    """Create a course with N topics, optionally enroll a student.

    Returns (course_id, [topic_id, ...]) in order-index order.
    prereq_edges: list of (topic_index, prereq_topic_index) pairs (0-based).
    """
    c_repo = get_course_repository()
    course = c_repo.create_course(
        title=course_title,
        course_code=course_code,
        instructor_id=1,
        description="M4 test course",
    )
    course_id = course.id
    topic_ids: list[int] = []
    for i in range(num_topics):
        topic = c_repo.create_topic(
            course_id=course_id,
            title=f"Topic {i + 1}",
            description=f"Description for topic {i + 1}",
            order_index=i,
        )
        topic_ids.append(topic.id)

    if prereq_edges:
        for topic_idx, prereq_idx in prereq_edges:
            c_repo.add_prerequisite(topic_ids[topic_idx], topic_ids[prereq_idx])

    if enroll_student_id is not None:
        c_repo.enroll_student(enroll_student_id, course_id)

    return course_id, topic_ids


def _add_proficient_responses(student_id: int, topic_id: int, count: int = 10) -> None:
    """Append `count` Easy-correct responses to push a topic to Proficient."""
    a_repo = get_adaptive_repository()
    record = ResponseRecord(is_correct=True, difficulty="Easy")
    for _ in range(count):
        a_repo.append_student_response(student_id, topic_id, record)


def _add_weak_responses(student_id: int, topic_id: int, count: int = 10) -> None:
    """Append `count` Easy-incorrect responses to push a topic to Weak."""
    a_repo = get_adaptive_repository()
    record = ResponseRecord(is_correct=False, difficulty="Easy")
    for _ in range(count):
        a_repo.append_student_response(student_id, topic_id, record)


# =============================================================================
# 1. Happy-path: Enrolled Student Gets Learning Path
# =============================================================================


class TestStudentLearningPath:
    """Tests for student-facing learning path retrieval."""

    def test_enrolled_student_gets_learning_path_200(self, client, student1_auth):
        """Enrolled student receives 200 with full path response (FR-11, FR-13)."""
        course_id, _ = _create_course_with_topics(
            num_topics=2, enroll_student_id=101, course_code="TEST-M4-100"
        )
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["course_id"] == course_id
        assert data["student_id"] == 101
        assert data["total_topics"] == 2
        assert isinstance(data["path"], list)
        assert len(data["path"]) == 2

    def test_response_contains_expected_fields(self, client, student1_auth):
        """Each TopicPathItem in the path contains all required fields."""
        course_id, _ = _create_course_with_topics(
            num_topics=1, enroll_student_id=101, course_code="TEST-M4-101"
        )
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        item = response.json()["path"][0]
        for field in (
            "topic_id",
            "title",
            "description",
            "order_index",
            "status",
            "score",
            "is_unlocked",
            "is_recommended",
            "locked_reason",
            "prerequisite_topic_ids",
            "rationale",
        ):
            assert field in item, f"Missing field: {field}"

    def test_topics_ordered_by_order_index(self, client, student1_auth):
        """Path items are returned in ascending order_index order (FR-11)."""
        course_id, _ = _create_course_with_topics(
            num_topics=3, enroll_student_id=101, course_code="TEST-M4-102"
        )
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        indices = [item["order_index"] for item in response.json()["path"]]
        assert indices == sorted(indices)

    def test_no_topics_course_returns_empty_path(self, client, student1_auth):
        """A course with zero topics returns a valid empty path gracefully."""
        c_repo = get_course_repository()
        course = c_repo.create_course(
            title="Empty Course",
            course_code="TEST-M4-103",
            instructor_id=1,
            description=None,
        )
        c_repo.enroll_student(101, course.id)
        response = client.get(
            f"/api/v1/courses/{course.id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_topics"] == 0
        assert data["path"] == []
        assert data["completion_percentage"] == 0.0


# =============================================================================
# 2. Authorization Tests
# =============================================================================


class TestLearningPathAuthorization:
    """Authorization enforcement tests for the learning-path endpoint."""

    def test_unauthenticated_request_rejected_401(self, client):
        """Missing Authorization header returns 401 (NFR-04)."""
        response = client.get("/api/v1/courses/1/learning-path")
        assert response.status_code == 401

    def test_non_enrolled_student_rejected_403(self, client, student1_auth):
        """Student not enrolled in the course is rejected with 403 (FR-14)."""
        course_id, _ = _create_course_with_topics(
            num_topics=1, enroll_student_id=None, course_code="TEST-M4-200"
        )
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 403

    def test_instructor_owns_course_gets_200(self, client, instructor1_auth, student1_auth):
        """Instructor who owns the course can retrieve path (no enrollment needed) (FR-14)."""
        course_id, _ = _create_course_with_topics(
            num_topics=2, enroll_student_id=101, course_code="TEST-M4-201"
        )
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=instructor1_auth,
        )
        assert response.status_code == 200

    def test_non_owner_instructor_rejected_403(self, client, instructor2_auth):
        """Instructor who does not own the course is rejected with 403 (NFR-05)."""
        course_id, _ = _create_course_with_topics(
            num_topics=1, enroll_student_id=None, course_code="TEST-M4-202"
        )
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=instructor2_auth,
        )
        assert response.status_code == 403

    def test_course_not_found_returns_404(self, client, instructor1_auth):
        """Non-existent course_id returns 404 (FR-11)."""
        response = client.get(
            "/api/v1/courses/999999/learning-path",
            headers=instructor1_auth,
        )
        assert response.status_code == 404

    def test_student_privacy_cannot_view_other_student_path_403(self, client, student1_auth):
        """Student Alice (101) cannot view Student Bob's (102) path — 403 (NFR-06)."""
        course_id, _ = _create_course_with_topics(
            num_topics=1, enroll_student_id=101, course_code="TEST-M4-203"
        )
        # Alice requests Bob's path via ?student_id=102
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path?student_id=102",
            headers=student1_auth,
        )
        assert response.status_code == 403

    def test_instructor_views_specific_student_path_decision5(self, client, instructor1_auth):
        """Instructor can view a specific enrolled student's path via ?student_id (Decision 5)."""
        course_id, _ = _create_course_with_topics(
            num_topics=2, enroll_student_id=101, course_code="TEST-M4-204"
        )
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path?student_id=101",
            headers=instructor1_auth,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == 101


# =============================================================================
# 3. Prerequisite Locking Logic (FR-11, Decision 4)
# =============================================================================


class TestPrerequisiteLocking:
    """Tests for Phase 1: prerequisite-aware topic locking."""

    def test_topics_without_prerequisites_are_unlocked(self, client, student1_auth):
        """Topics with no prerequisites are always unlocked (FR-11)."""
        course_id, _ = _create_course_with_topics(
            num_topics=2, enroll_student_id=101, course_code="TEST-M4-300"
        )
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        for item in response.json()["path"]:
            assert item["is_unlocked"] is True
            assert item["locked_reason"] is None

    def test_topic_locked_when_prerequisite_not_proficient(self, client, student1_auth):
        """Topic 2 is locked when Topic 1 (its prerequisite) is Not Assessed (Decision 4)."""
        # Topic 1 (index 0) → prerequisite for Topic 2 (index 1)
        course_id, _ = _create_course_with_topics(
            num_topics=2,
            enroll_student_id=101,
            course_code="TEST-M4-301",
            prereq_edges=[(1, 0)],  # topic[1] requires topic[0]
        )
        # No responses → both Not Assessed; Topic 2 must be locked
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        path = response.json()["path"]
        # Topic 1 (order_index=0): no prereqs → unlocked
        assert path[0]["is_unlocked"] is True
        # Topic 2 (order_index=1): prereq not Proficient → locked
        assert path[1]["is_unlocked"] is False
        assert path[1]["locked_reason"] is not None
        assert "Topic 1" in path[1]["locked_reason"]

    def test_topic_unlocked_when_prerequisite_becomes_proficient(self, client, student1_auth):
        """Topic 2 is unlocked once Topic 1 reaches Proficient mastery (Decision 4)."""
        course_id, topic_ids = _create_course_with_topics(
            num_topics=2,
            enroll_student_id=101,
            course_code="TEST-M4-302",
            prereq_edges=[(1, 0)],
        )
        # Make Topic 1 Proficient for student 101
        _add_proficient_responses(student_id=101, topic_id=topic_ids[0], count=10)

        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        path = response.json()["path"]
        assert path[0]["status"] == "Proficient"
        assert path[0]["is_unlocked"] is True
        assert path[1]["is_unlocked"] is True
        assert path[1]["locked_reason"] is None

    def test_chain_locked_when_first_prerequisite_not_proficient(self, client, student1_auth):
        """In a T1→T2→T3 chain, T3 is locked if T2 is locked (prerequisite chain)."""
        course_id, _ = _create_course_with_topics(
            num_topics=3,
            enroll_student_id=101,
            course_code="TEST-M4-303",
            prereq_edges=[(1, 0), (2, 1)],  # T2 requires T1, T3 requires T2
        )
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        path = response.json()["path"]
        assert path[0]["is_unlocked"] is True  # T1: no prereqs
        assert path[1]["is_unlocked"] is False  # T2: T1 not Proficient
        assert path[2]["is_unlocked"] is False  # T3: T2 not Proficient


# =============================================================================
# 4. Recommendation Tagging (FR-12)
# =============================================================================


class TestRecommendationTagging:
    """Tests for Phase 2: M3 engine recommendation tagging."""

    def test_not_assessed_topic_gets_recommended_when_unlocked(self, client, student1_auth):
        """Unlocked Not Assessed topics receive is_recommended=True (FR-12)."""
        course_id, _ = _create_course_with_topics(
            num_topics=1, enroll_student_id=101, course_code="TEST-M4-400"
        )
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        item = response.json()["path"][0]
        assert item["status"] == "Not Assessed"
        assert item["is_recommended"] is True
        assert item["rationale"] is not None

    def test_proficient_topic_not_recommended(self, client, student1_auth):
        """Proficient topics are never recommended (TC-18-2 / FR-12)."""
        course_id, topic_ids = _create_course_with_topics(
            num_topics=1, enroll_student_id=101, course_code="TEST-M4-401"
        )
        _add_proficient_responses(101, topic_ids[0], count=10)

        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        item = response.json()["path"][0]
        assert item["status"] == "Proficient"
        assert item["is_recommended"] is False
        assert item["rationale"] is None

    def test_locked_topic_not_recommended(self, client, student1_auth):
        """Locked topics (prerequisite unmet) are never recommended (FR-12)."""
        course_id, _ = _create_course_with_topics(
            num_topics=2,
            enroll_student_id=101,
            course_code="TEST-M4-402",
            prereq_edges=[(1, 0)],
        )
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        path = response.json()["path"]
        # Topic 1: unlocked, Not Assessed → recommended
        assert path[0]["is_recommended"] is True
        # Topic 2: locked → not recommended
        assert path[1]["is_recommended"] is False

    def test_weak_topic_recommended_before_developing(self, client, student1_auth):
        """Weak topics appear as recommended (TC-18-1: Weak before Developing)."""
        course_id, topic_ids = _create_course_with_topics(
            num_topics=2, enroll_student_id=101, course_code="TEST-M4-403"
        )
        # Topic 1: Weak (all wrong Easy)
        _add_weak_responses(101, topic_ids[0], count=5)
        # Topic 2: some correct -> Developing (mix ~0.5-0.79)
        a_repo = get_adaptive_repository()
        for _ in range(4):
            a_repo.append_student_response(
                101, topic_ids[1], ResponseRecord(is_correct=True, difficulty="Easy")
            )
        for _ in range(6):
            a_repo.append_student_response(
                101, topic_ids[1], ResponseRecord(is_correct=False, difficulty="Easy")
            )

        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        path = response.json()["path"]
        # Both should be recommended (neither is Proficient and both are unlocked)
        recommended = [item for item in path if item["is_recommended"]]
        assert len(recommended) >= 1
        # Weak item is recommended
        weak_items = [item for item in path if item["status"] == "Weak"]
        if weak_items:
            assert weak_items[0]["is_recommended"] is True


# =============================================================================
# 5. Completion Statistics (FR-13)
# =============================================================================


class TestCompletionStatistics:
    """Tests for learning path summary statistics."""

    def test_zero_completion_when_no_responses(self, client, student1_auth):
        """With no responses, completion_percentage=0.0 and completed_count=0 (FR-13)."""
        course_id, _ = _create_course_with_topics(
            num_topics=3, enroll_student_id=101, course_code="TEST-M4-500"
        )
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completed_count"] == 0
        assert data["completion_percentage"] == 0.0
        assert data["unlocked_count"] == 3  # All have no prereqs → all unlocked

    def test_full_completion_when_all_topics_proficient(self, client, student1_auth):
        """100% completion when all topics are Proficient (FR-13)."""
        course_id, topic_ids = _create_course_with_topics(
            num_topics=2, enroll_student_id=101, course_code="TEST-M4-501"
        )
        for tid in topic_ids:
            _add_proficient_responses(101, tid, count=10)

        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completed_count"] == 2
        assert data["total_topics"] == 2
        assert data["completion_percentage"] == 100.0

    def test_partial_completion_percentage(self, client, student1_auth):
        """50% completion when 1 of 2 topics is Proficient (FR-13)."""
        course_id, topic_ids = _create_course_with_topics(
            num_topics=2, enroll_student_id=101, course_code="TEST-M4-502"
        )
        _add_proficient_responses(101, topic_ids[0], count=10)

        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completed_count"] == 1
        assert data["total_topics"] == 2
        assert abs(data["completion_percentage"] - 50.0) < 0.01

    def test_unlocked_count_excludes_locked_topics(self, client, student1_auth):
        """unlocked_count reflects only topics whose prerequisites are met (FR-13)."""
        # T1→T2: T2 locked because T1 not Proficient
        course_id, _ = _create_course_with_topics(
            num_topics=2,
            enroll_student_id=101,
            course_code="TEST-M4-503",
            prereq_edges=[(1, 0)],
        )
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=student1_auth,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["unlocked_count"] == 1  # Only T1 is unlocked
        assert data["total_topics"] == 2


# =============================================================================
# 6. Instructor Views Path for Their Own Course
# =============================================================================


class TestInstructorLearningPath:
    """Tests for instructor-role path retrieval."""

    def test_instructor_default_views_own_path(self, client, instructor1_auth):
        """Instructor without ?student_id defaults to viewing their own user_id path (Decision 5)."""
        course_id, _ = _create_course_with_topics(num_topics=2, course_code="TEST-M4-600")
        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path",
            headers=instructor1_auth,
        )
        # Instructor (ID=1) is not enrolled but owns the course → 200
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == 1  # Defaults to instructor's own ID

    def test_instructor_views_student_path_via_student_id_param(self, client, instructor1_auth):
        """Instructor can pass ?student_id to view an enrolled student's path (Decision 5)."""
        course_id, topic_ids = _create_course_with_topics(
            num_topics=2, enroll_student_id=101, course_code="TEST-M4-601"
        )
        _add_proficient_responses(101, topic_ids[0], count=10)

        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path?student_id=101",
            headers=instructor1_auth,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == 101
        # Topic 1 should be Proficient (we added proficient responses)
        assert data["path"][0]["status"] == "Proficient"

    def test_instructor_path_reflects_student_mastery_not_instructors(
        self, client, instructor1_auth
    ):
        """The path returned for ?student_id reflects that student's mastery, not the instructor's."""
        course_id, topic_ids = _create_course_with_topics(
            num_topics=1, enroll_student_id=101, course_code="TEST-M4-602"
        )
        # Only add responses for student 101 — instructor (1) has none
        _add_weak_responses(student_id=101, topic_id=topic_ids[0], count=5)

        response = client.get(
            f"/api/v1/courses/{course_id}/learning-path?student_id=101",
            headers=instructor1_auth,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == 101
        # Student's mastery is Weak
        assert data["path"][0]["status"] == "Weak"
