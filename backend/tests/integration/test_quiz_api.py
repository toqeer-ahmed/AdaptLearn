"""Integration tests for Module 2 Quiz & Assessment Engine HTTP API endpoints.

Requirements Traceability:
- FR-08: POST /courses/{id}/questions, PATCH /questions/{id}, DELETE /questions/{id}.
- FR-10: POST /courses/{id}/quizzes, POST /quizzes/{id}/publish, GET /courses/{id}/quizzes.
- FR-11: GET /quizzes/{id} (student-safe).
- FR-12: POST /courses/{id}/topics/{id}/practice-quiz.
- FR-13: POST /quizzes/{id}/attempts (atomic submission & automated grading).
- FR-14: GET /attempts/{id} (result viewing & privacy).
- NFR-05 & NFR-06: Server-side RBAC and data privacy.
- NFR-08: Transactional persistence.
"""
from pathlib import Path
import tempfile

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.quizzes import router as quizzes_router
from app.core.auth import get_current_user
from app.db.base import Base
from app.db.session import init_db
from app.repositories.adaptive_repository import AdaptiveRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.quiz_repository import QuizRepository
from app.services.quiz_service import QuizService, get_quiz_service


@pytest.fixture
def test_env():
    """Create isolated database, repositories, service, and FastAPI TestClient."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    init_db(target_engine=engine)

    quiz_repo = QuizRepository(session_factory=session_factory)
    prog_repo = ProgressRepository(session_factory=session_factory)
    adapt_repo = AdaptiveRepository(session_factory=session_factory)
    service = QuizService(
        quiz_repository=quiz_repo,
        progress_repository=prog_repo,
        adaptive_repository=adapt_repo,
        session_factory=session_factory,
    )

    app = FastAPI(title="Test AdaptLearn Quiz Engine")
    app.include_router(quizzes_router, prefix="/api/v1")

    # Dependency overrides for service
    app.dependency_overrides[get_quiz_service] = lambda: service

    # Setup default personas
    prog_repo.set_course_owner(course_id=1, instructor_id=1)
    prog_repo.enroll_student(student_id=101, course_id=1)

    client = TestClient(app)

    yield {
        "client": client,
        "app": app,
        "service": service,
        "prog_repo": prog_repo,
        "session_factory": session_factory,
    }

    engine.dispose()
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            pass


class TestQuizApiQuestionBank:
    """Test Question Bank HTTP endpoints (FR-08, FR-09)."""

    def test_create_question_api_instructor_success(self, test_env):
        client = test_env["client"]
        # Use development bearer token format supported by auth.py
        headers = {"Authorization": "Bearer token-1-instructor"}
        payload = {
            "statement": "What is equivalence partitioning?",
            "options": ["A testing technique", "A compiler pass", "A hardware bus"],
            "correct_option_index": 0,
            "difficulty": "Medium",
            "explanation": "Black-box testing method.",
        }
        res = client.post("/api/v1/courses/1/questions?topic_id=2", json=payload, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["id"] is not None
        assert data["statement"] == "What is equivalence partitioning?"
        assert data["correct_option_index"] == 0
        assert data["difficulty"] == "Medium"
        assert data["is_active"] is True

    def test_create_question_api_student_forbidden(self, test_env):
        client = test_env["client"]
        headers = {"Authorization": "Bearer token-101-student"}
        payload = {
            "statement": "Student trying to add question",
            "options": ["A", "B"],
            "correct_option_index": 0,
            "difficulty": "Easy",
        }
        res = client.post("/api/v1/courses/1/questions", json=payload, headers=headers)
        assert res.status_code == 403

    def test_update_and_delete_question_api(self, test_env):
        client = test_env["client"]
        headers = {"Authorization": "Bearer token-1-instructor"}

        # 1. Create
        create_res = client.post(
            "/api/v1/courses/1/questions",
            json={"statement": "Original", "options": ["A", "B"], "correct_option_index": 0, "difficulty": "Easy"},
            headers=headers,
        )
        assert create_res.status_code == 201
        qid = create_res.json()["id"]

        # 2. Update
        update_res = client.patch(
            f"/api/v1/questions/{qid}",
            json={"statement": "Updated", "difficulty": "Hard"},
            headers=headers,
        )
        assert update_res.status_code == 200
        assert update_res.json()["statement"] == "Updated"
        assert update_res.json()["difficulty"] == "Hard"

        # 3. Delete (hard delete since unanswered)
        del_res = client.delete(f"/api/v1/questions/{qid}", headers=headers)
        assert del_res.status_code == 200
        assert del_res.json()["deleted"] is True


class TestQuizApiTakingAndGrading:
    """Test full Quiz taking, submission, and result display lifecycle (FR-10..FR-14)."""

    def test_end_to_end_quiz_lifecycle(self, test_env):
        client = test_env["client"]
        inst_headers = {"Authorization": "Bearer token-1-instructor"}
        stud_headers = {"Authorization": "Bearer token-101-student"}

        # Step 1: Instructor creates two questions
        q1_res = client.post(
            "/api/v1/courses/1/questions?topic_id=1",
            json={"statement": "Q1", "options": ["True", "False"], "correct_option_index": 0, "difficulty": "Easy"},
            headers=inst_headers,
        )
        q2_res = client.post(
            "/api/v1/courses/1/questions?topic_id=2",
            json={"statement": "Q2", "options": ["Red", "Green", "Blue"], "correct_option_index": 1, "difficulty": "Medium"},
            headers=inst_headers,
        )
        q1_id = q1_res.json()["id"]
        q2_id = q2_res.json()["id"]

        # Step 2: Instructor creates quiz
        quiz_res = client.post(
            "/api/v1/courses/1/quizzes",
            json={"title": "Midterm Exam", "question_ids": [q1_id, q2_id], "is_published": False},
            headers=inst_headers,
        )
        assert quiz_res.status_code == 201
        quiz_id = quiz_res.json()["id"]

        # Step 3: Student attempts unpublished quiz -> rejected
        get_res_1 = client.get(f"/api/v1/quizzes/{quiz_id}", headers=stud_headers)
        assert get_res_1.status_code == 400

        # Step 4: Instructor publishes quiz
        pub_res = client.post(f"/api/v1/quizzes/{quiz_id}/publish?is_published=true", headers=inst_headers)
        assert pub_res.status_code == 200
        assert pub_res.json()["is_published"] is True

        # Step 5: Student retrieves student-safe quiz
        get_res_2 = client.get(f"/api/v1/quizzes/{quiz_id}", headers=stud_headers)
        assert get_res_2.status_code == 200
        safe_data = get_res_2.json()
        assert len(safe_data["questions"]) == 2
        for q in safe_data["questions"]:
            assert "correct_option_index" not in q
            assert "explanation" not in q

        # Step 6: Student submits answers: Q1 correct (0), Q2 incorrect (0)
        submit_payload = {
            "answers": [
                {"question_id": q1_id, "selected_option_index": 0},
                {"question_id": q2_id, "selected_option_index": 0},
            ]
        }
        submit_res = client.post(f"/api/v1/quizzes/{quiz_id}/attempts", json=submit_payload, headers=stud_headers)
        assert submit_res.status_code == 201
        result = submit_res.json()
        assert result["score"] == 0.5  # 1 out of 2 correct
        assert result["correct_answers"] == 1
        assert len(result["answers"]) == 2
        assert len(result["topic_scores"]) == 2
        attempt_id = result["attempt_id"]

        # Step 7: Student views attempt result (FR-14)
        view_res = client.get(f"/api/v1/attempts/{attempt_id}", headers=stud_headers)
        assert view_res.status_code == 200
        view_data = view_res.json()
        assert view_data["score"] == 0.5
        assert view_data["answers"][0]["is_correct"] is True
        assert view_data["answers"][1]["is_correct"] is False

        # Step 8: Other student (102) forbidden from viewing (NFR-06)
        other_stud_headers = {"Authorization": "Bearer token-102-student"}
        test_env["prog_repo"].enroll_student(student_id=102, course_id=1)
        forbidden_res = client.get(f"/api/v1/attempts/{attempt_id}", headers=other_stud_headers)
        assert forbidden_res.status_code == 403
