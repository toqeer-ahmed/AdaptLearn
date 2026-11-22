"""Cross-Module Integration and Regression Tests (AdaptLearn INT-01).

Requirements Traceability & Cross-Module Boundaries:
- M1 (User & Course Management): Enrollment validation, authentication, role verification (FR-01..FR-03).
- M2 (Quiz & Assessment Engine): Quiz attempt submission and question response forwarding (FR-11..FR-15).
- M3 (Adaptive Learning Engine): Mastery score calculation and pedagogical recommendation generation (FR-16..FR-20).
- M4 (Personalized Learning Paths): Prerequisite-aware recommendation sequencing (FR-18, TC-18-3).
- M5 (Progress Analytics & Dashboard): Student progress dashboard, attempt history, and instructor analytics (FR-21..FR-24).
- Quality & Non-Functional:
  - NFR-04: Bearer token authentication on all protected endpoints.
  - NFR-05 & NFR-15: Strict architectural layering (Router -> Service -> Repository; Service -> Engine).
  - NFR-06: Strict privacy and multi-tenant authorization boundaries.
  - NFR-08: Deterministic calculations and zero fabricated metrics.
"""

import pytest
from fastapi.testclient import TestClient

from app.engine.recommendation_strategy import TopicRecommendationInput
from app.main import app
from app.repositories.adaptive_repository import get_adaptive_repository
from app.repositories.course_repository import get_course_repository
from app.repositories.progress_repository import (
    AttemptRecord,
    get_progress_repository,
)


@pytest.fixture(autouse=True)
def reset_repositories():
    """Ensure in-memory repository stores are cleanly reset before and after each test."""
    p_repo = get_progress_repository()
    a_repo = get_adaptive_repository()
    c_repo = get_course_repository()
    p_repo.clear()
    a_repo.clear()
    c_repo.clear()
    yield
    p_repo.clear()
    a_repo.clear()
    c_repo.clear()


@pytest.fixture
def client():
    """FastAPI test client instance."""
    return TestClient(app)


class TestCrossModuleEndToEndPipeline:
    """Verify end-to-end integration across M1, M2, M3, M4, and M5."""

    def test_full_student_lifecycle_quiz_to_mastery_to_dashboard(self, client):
        """Lifecycle test:

        1. Setup Course & Topics (M1/M3).
        2. Student enrolls in Course (M1).
        3. Initial Progress check reveals Not Assessed / 0% completion (M5).
        4. Student submits Quiz responses via M2 -> M3 recalculates mastery.
        5. Progress dashboard updates completion percentage and recommendations (M5/M4).
        6. Instructor analytics accurately aggregates student mastery & question stats (M5).
        """
        p_repo = get_progress_repository()
        a_repo = get_adaptive_repository()

        course_id = 201
        student_id = 42
        instructor_id = 99

        # Step 1: Course Setup (M1/M3)
        p_repo.set_course_owner(course_id=course_id, instructor_id=instructor_id)
        p_repo.enroll_student(student_id=student_id, course_id=course_id)

        # 3 Topics: 1: Basics (prereq for 2), 2: Loops, 3: Functions
        a_repo.set_course_topics(
            course_id,
            [
                TopicRecommendationInput(topic_id=1, name="Basics", mastery_level="Not Assessed", score=0.0),
                TopicRecommendationInput(topic_id=2, name="Loops", mastery_level="Not Assessed", score=0.0, prerequisites={1}),
                TopicRecommendationInput(topic_id=3, name="Functions", mastery_level="Not Assessed", score=0.0),
            ],
        )

        student_headers = {"Authorization": f"Bearer token-{student_id}-student"}
        instructor_headers = {"Authorization": f"Bearer token-{instructor_id}-instructor"}

        # Step 2: Verify Initial Student Progress (M5)
        init_progress = client.get(f"/api/v1/courses/{course_id}/progress", headers=student_headers)
        assert init_progress.status_code == 200
        init_data = init_progress.json()
        assert init_data["completion_percentage"] == 0.0
        assert len(init_data["topic_breakdown"]) == 3
        for t in init_data["topic_breakdown"]:
            assert t["mastery_level"] == "Not Assessed"

        # Step 3: Simulate M2 Quiz Submission -> M3 Mastery Recalculation
        # Student answers 3 questions on Basics: 3 Hard questions, all correct -> Score = 1.0 (Proficient)
        attempt_payload = {
            "student_id": student_id,
            "course_id": course_id,
            "responses": [
                {"question_id": 101, "topic_id": 1, "is_correct": True, "difficulty": "Hard"},
                {"question_id": 102, "topic_id": 1, "is_correct": True, "difficulty": "Hard"},
                {"question_id": 103, "topic_id": 1, "is_correct": True, "difficulty": "Hard"},
                # 3 questions on Loops: 3 Easy questions, all incorrect -> Score = 0.0 (Weak)
                {"question_id": 201, "topic_id": 2, "is_correct": False, "difficulty": "Easy"},
                {"question_id": 202, "topic_id": 2, "is_correct": False, "difficulty": "Easy"},
                {"question_id": 203, "topic_id": 2, "is_correct": False, "difficulty": "Easy"},
            ],
        }

        recalc_res = client.post(
            f"/api/v1/courses/{course_id}/recalculate-mastery",
            json=attempt_payload,
        )
        assert recalc_res.status_code == 200
        recalc_data = recalc_res.json()
        assert recalc_data["student_id"] == student_id
        assert len(recalc_data["updated_topics"]) == 2

        # Basics is Proficient (1.0), Loops is Weak (0.0)
        topic_1_res = next(t for t in recalc_data["updated_topics"] if t["topic_id"] == 1)
        topic_2_res = next(t for t in recalc_data["updated_topics"] if t["topic_id"] == 2)
        assert topic_1_res["level"] == "Proficient"
        assert topic_1_res["score"] == 1.0
        assert topic_2_res["level"] == "Weak"
        assert topic_2_res["score"] == 0.0

        # Also record attempt in M5 history & question statistics
        p_repo.record_attempt(
            AttemptRecord(
                attempt_id=1,
                student_id=student_id,
                course_id=course_id,
                quiz_id=10,
                quiz_title="Module Quiz 1",
                score=3.0,
                total_questions=6,
                submitted_at="2026-11-21T05:00:00Z",
            )
        )
        p_repo.record_question_response(
            course_id=course_id,
            question_id=101,
            question_text="Basics Q1",
            topic_id=1,
            topic_name="Basics",
            difficulty="Hard",
            is_correct=True,
        )
        p_repo.record_question_response(
            course_id=course_id,
            question_id=201,
            question_text="Loops Q1",
            topic_id=2,
            topic_name="Loops",
            difficulty="Easy",
            is_correct=False,
        )

        # Step 4: Verify Student Dashboard Post-Quiz (M5)
        updated_progress = client.get(f"/api/v1/courses/{course_id}/progress", headers=student_headers)
        assert updated_progress.status_code == 200
        prog_data = updated_progress.json()

        # 1 out of 3 topics proficient -> 33.3% completion
        assert prog_data["completion_percentage"] == 33.3
        assert len(prog_data["recent_attempts"]) == 1
        assert prog_data["recent_attempts"][0]["score"] == 3.0

        # Recommendations: Loops is Weak, its prerequisite Basics is Proficient -> Loops is recommended!
        recs = prog_data["recommended_topics"]
        assert len(recs) > 0
        assert recs[0]["topic_id"] == 2
        assert recs[0]["mastery_level"] == "Weak"
        assert "remediation" in recs[0]["rationale"].lower() or "practice" in recs[0]["rationale"].lower()

        # Step 5: Verify Instructor Analytics (M5)
        # Mastery Distribution (FR-23)
        dist_res = client.get(f"/api/v1/courses/{course_id}/analytics/mastery-distribution", headers=instructor_headers)
        assert dist_res.status_code == 200
        dist_data = dist_res.json()
        assert dist_data["total_enrolled"] == 1

        t1_dist = next(t for t in dist_data["topics"] if t["topic_id"] == 1)
        t2_dist = next(t for t in dist_data["topics"] if t["topic_id"] == 2)
        t3_dist = next(t for t in dist_data["topics"] if t["topic_id"] == 3)

        assert t1_dist["proficient_count"] == 1
        assert t2_dist["weak_count"] == 1
        assert t3_dist["not_assessed_count"] == 1

        # Student Roster Matrix (FR-22)
        roster_res = client.get(f"/api/v1/courses/{course_id}/analytics/student-roster", headers=instructor_headers)
        assert roster_res.status_code == 200
        roster_data = roster_res.json()
        assert len(roster_data["students"]) == 1
        student_roster_entry = roster_data["students"][0]
        assert student_roster_entry["student_id"] == student_id
        assert len(student_roster_entry["topic_masteries"]) == 3

        # Question Performance Statistics (FR-24)
        q_stats_res = client.get(f"/api/v1/courses/{course_id}/analytics/questions", headers=instructor_headers)
        assert q_stats_res.status_code == 200
        q_data = q_stats_res.json()
        assert len(q_data["questions"]) == 2
        q101 = next(q for q in q_data["questions"] if q["question_id"] == 101)
        q201 = next(q for q in q_data["questions"] if q["question_id"] == 201)
        assert q101["correct_percentage"] == 100.0
        assert q201["correct_percentage"] == 0.0


class TestCrossModuleAuthorizationAndSecurity:
    """Verify security, authentication, and role authorization contracts across all endpoints."""

    def test_unauthenticated_requests_fail_consistently(self, client):
        """Protected endpoints across all modules must reject missing tokens with 401."""
        endpoints = [
            ("GET", "/api/v1/courses/100/progress"),
            ("GET", "/api/v1/courses/100/attempts"),
            ("GET", "/api/v1/courses/100/analytics/mastery-distribution"),
            ("GET", "/api/v1/courses/100/analytics/student-roster"),
            ("GET", "/api/v1/courses/100/analytics/questions"),
        ]
        for method, path in endpoints:
            if method == "GET":
                res = client.get(path)
            assert res.status_code == 401, f"Expected 401 on {path}, got {res.status_code}"

    def test_student_cannot_access_instructor_analytics(self, client):
        """Role isolation (FR-03, TC-03-1): Student persona receives 403 Forbidden on instructor endpoints."""
        student_headers = {"Authorization": "Bearer token-5-student"}
        instructor_endpoints = [
            "/api/v1/courses/100/analytics/mastery-distribution",
            "/api/v1/courses/100/analytics/student-roster",
            "/api/v1/courses/100/analytics/questions",
        ]
        for path in instructor_endpoints:
            res = client.get(path, headers=student_headers)
            assert res.status_code == 403, f"Expected 403 for student on {path}, got {res.status_code}"

    def test_instructor_course_ownership_enforcement(self, client):
        """Multi-tenant isolation (TC-22-2): Instructor cannot access analytics for courses owned by another instructor."""
        p_repo = get_progress_repository()
        course_id = 888
        p_repo.set_course_owner(course_id=course_id, instructor_id=1)  # Owned by Instructor 1

        unauthorized_instructor_headers = {"Authorization": "Bearer token-2-instructor"}  # Instructor 2
        res = client.get(f"/api/v1/courses/{course_id}/analytics/mastery-distribution", headers=unauthorized_instructor_headers)
        assert res.status_code == 403
        assert "does not own" in res.json()["error"]["message"].lower()

    def test_student_privacy_isolation(self, client):
        """Student privacy (NFR-06): Student cannot query another student's progress or attempts."""
        p_repo = get_progress_repository()
        course_id = 555
        student_a = 10
        student_b = 20

        p_repo.enroll_student(student_id=student_a, course_id=course_id)
        p_repo.enroll_student(student_id=student_b, course_id=course_id)

        # Student A tries to query progress specifying Student B's ID via query parameter
        headers_a = {"Authorization": f"Bearer token-{student_a}-student"}
        res = client.get(f"/api/v1/courses/{course_id}/progress?student_id={student_b}", headers=headers_a)
        assert res.status_code == 403
        assert "another student" in res.json()["error"]["message"].lower()


class TestCanonicalCourseTopicCrossModuleIntegration:
    """Validate GAP-03: Courses and topics created via M1 are fully visible to M3 and M5."""

    def test_m1_created_course_and_topics_visible_to_m3_and_m5(self, client):
        """End-to-end integration:
        1. Create course and topics via M1 CourseRepository.
        2. Verify M3 recommendations returns canonical topics with prerequisite order.
        3. Verify M5 student progress dashboard displays canonical topics and calculates completion.
        4. Verify M5 instructor analytics (mastery distribution & student roster) displays canonical topics.
        """
        c_repo = get_course_repository()
        p_repo = get_progress_repository()

        instructor_id = 1
        student_id = 42
        instructor_headers = {"Authorization": f"Bearer token-{instructor_id}-instructor"}
        student_headers = {"Authorization": f"Bearer token-{student_id}-student"}

        # Step 1: Create M1 Course
        course = c_repo.create_course(
            title="Data Structures & Algorithms",
            course_code="CS201",
            instructor_id=instructor_id,
            description="Authoritative M1 curriculum course",
        )
        course_id = course.id

        # Step 2: Create M1 Topics with sequential ordering
        top_arrays = c_repo.create_topic(course_id=course_id, title="Arrays & Lists", order_index=0)
        top_stacks = c_repo.create_topic(course_id=course_id, title="Stacks & Queues", order_index=1)
        top_trees = c_repo.create_topic(course_id=course_id, title="Binary Trees", order_index=2)

        # Step 3: Add Prerequisites: Stacks requires Arrays; Trees requires Stacks
        c_repo.add_prerequisite(topic_id=top_stacks.id, prerequisite_topic_id=top_arrays.id)
        c_repo.add_prerequisite(topic_id=top_trees.id, prerequisite_topic_id=top_stacks.id)

        # Step 4: Enroll student in course
        p_repo.enroll_student(student_id=student_id, course_id=course_id)
        p_repo.set_course_owner(course_id=course_id, instructor_id=instructor_id)

        # Step 5: Verify M3 Recommendations (GET /api/v1/courses/{id}/recommendations)
        rec_res = client.get(f"/api/v1/courses/{course_id}/recommendations")
        assert rec_res.status_code == 200
        rec_data = rec_res.json()
        assert rec_data["course_id"] == course_id
        assert rec_data["total_recommended"] >= 1
        rec_names = [r["topic_name"] for r in rec_data["recommendations"]]
        # "Arrays & Lists" has no prerequisites and is Not Assessed -> should be recommended
        assert "Arrays & Lists" in rec_names
        # First recommended topic should be "Arrays & Lists" (foundational starting point)
        assert rec_names[0] == "Arrays & Lists"

        # Step 6: Verify M5 Student Progress Dashboard (GET /api/v1/courses/{id}/progress)
        prog_res = client.get(f"/api/v1/courses/{course_id}/progress", headers=student_headers)
        assert prog_res.status_code == 200
        prog_data = prog_res.json()
        assert prog_data["course_id"] == course_id
        assert prog_data["completion_percentage"] == 0.0
        assert len(prog_data["topic_breakdown"]) == 3
        breakdown_names = [t["topic_name"] for t in prog_data["topic_breakdown"]]
        assert breakdown_names == ["Arrays & Lists", "Stacks & Queues", "Binary Trees"]

        # Step 7: Verify M5 Instructor Analytics - Mastery Distribution
        dist_res = client.get(
            f"/api/v1/courses/{course_id}/analytics/mastery-distribution",
            headers=instructor_headers,
        )
        assert dist_res.status_code == 200
        dist_data = dist_res.json()
        assert dist_data["total_enrolled"] == 1
        assert len(dist_data["topics"]) == 3
        dist_names = [t["topic_name"] for t in dist_data["topics"]]
        assert dist_names == ["Arrays & Lists", "Stacks & Queues", "Binary Trees"]
        for topic_dist in dist_data["topics"]:
            assert topic_dist["not_assessed_count"] == 1
            assert topic_dist["total_students"] == 1

        # Step 8: Verify M5 Instructor Analytics - Student Roster Matrix
        roster_res = client.get(
            f"/api/v1/courses/{course_id}/analytics/student-roster",
            headers=instructor_headers,
        )
        assert roster_res.status_code == 200
        roster_data = roster_res.json()
        assert len(roster_data["students"]) == 1
        student_entry = roster_data["students"][0]
        assert student_entry["student_id"] == student_id
        assert len(student_entry["topic_masteries"]) == 3
        roster_topic_names = [tm["topic_name"] for tm in student_entry["topic_masteries"]]
        assert roster_topic_names == ["Arrays & Lists", "Stacks & Queues", "Binary Trees"]
