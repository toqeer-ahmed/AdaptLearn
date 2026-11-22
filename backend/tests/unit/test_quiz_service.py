"""Unit tests for Module 2 QuizService (FR-08 through FR-14, NFR-05, NFR-06, NFR-08).

Requirements Traceability:
- FR-08: Question authoring, update, and retrieval by authorized course owners.
- FR-09: Soft-deletion enforcement on answered questions.
- FR-10: Quiz creation, question ordering, and publishing guards.
- FR-11: Student-safe quiz taking omitting correct answers.
- FR-12: On-demand dynamic topic practice quiz generation.
- FR-13: Quiz attempt submission, automated grading, and atomic transaction.
- FR-14: Attempt result viewing with cross-student privacy enforcement.
- NFR-05: Server-side RBAC (course ownership and student enrollment).
- NFR-06: Cross-student data privacy.
- NFR-08: Transactional atomicity (attempt + answers + stats + adaptive updates).
"""

import contextlib
import tempfile
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import init_db
from app.models.adaptive import StudentTopicResponseModel
from app.models.progress import AttemptModel, QuestionStatsModel
from app.models.quiz import AttemptAnswerModel
from app.repositories.adaptive_repository import AdaptiveRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.quiz_repository import AnswerRecordInput, QuizRepository
from app.schemas.quiz import (
    AnswerSubmissionItem,
    PracticeQuizRequest,
    QuestionCreate,
    QuestionUpdate,
    QuizAttemptSubmitRequest,
    QuizCreate,
)
from app.services.quiz_service import QuizService


@pytest.fixture
def temp_db():
    """Create isolated SQLite database for service unit tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    init_db(target_engine=engine)

    yield session_factory, engine

    engine.dispose()
    if db_path.exists():
        with contextlib.suppress(PermissionError):
            db_path.unlink()


class TestQuizServiceQuestionBank:
    """Test QuizService business rules and access control for question authoring (FR-08, FR-09)."""

    def test_create_question_authorized_course_owner(self, temp_db):
        session_factory, _ = temp_db
        quiz_repo = QuizRepository(session_factory=session_factory)
        prog_repo = ProgressRepository(session_factory=session_factory)
        prog_repo.set_course_owner(course_id=1, instructor_id=1)

        service = QuizService(
            quiz_repository=quiz_repo,
            progress_repository=prog_repo,
            session_factory=session_factory,
        )
        payload = QuestionCreate(
            statement="What is test-driven development?",
            options=["Write tests first", "Write code first", "No tests needed"],
            correct_option_index=0,
            difficulty="Easy",
            explanation="TDD follows Red-Green-Refactor.",
        )

        res = service.create_question(course_id=1, payload=payload, instructor_id=1)
        assert res.id is not None
        assert res.statement == "What is test-driven development?"
        assert res.correct_option_index == 0
        assert res.difficulty == "Easy"
        assert res.is_active is True

    def test_create_question_unauthorized_instructor_rejected(self, temp_db):
        session_factory, _ = temp_db
        quiz_repo = QuizRepository(session_factory=session_factory)
        prog_repo = ProgressRepository(session_factory=session_factory)
        prog_repo.set_course_owner(course_id=1, instructor_id=1)

        service = QuizService(
            quiz_repository=quiz_repo,
            progress_repository=prog_repo,
            session_factory=session_factory,
        )
        payload = QuestionCreate(
            statement="Question statement",
            options=["A", "B"],
            correct_option_index=0,
            difficulty="Medium",
        )

        with pytest.raises(HTTPException) as exc:
            service.create_question(course_id=1, payload=payload, instructor_id=2)
        assert exc.value.status_code == 403
        assert "not the owner of course" in exc.value.detail

    def test_update_question_success(self, temp_db):
        session_factory, _ = temp_db
        quiz_repo = QuizRepository(session_factory=session_factory)
        prog_repo = ProgressRepository(session_factory=session_factory)
        prog_repo.set_course_owner(course_id=1, instructor_id=1)
        service = QuizService(
            quiz_repository=quiz_repo,
            progress_repository=prog_repo,
            session_factory=session_factory,
        )

        created = service.create_question(
            course_id=1,
            payload=QuestionCreate(
                statement="Original statement",
                options=["Opt 1", "Opt 2"],
                correct_option_index=0,
                difficulty="Easy",
            ),
            instructor_id=1,
        )

        updated = service.update_question(
            question_id=created.id,
            payload=QuestionUpdate(statement="Updated statement", difficulty="Hard"),
            instructor_id=1,
        )
        assert updated.statement == "Updated statement"
        assert updated.difficulty == "Hard"

    def test_update_question_not_found(self, temp_db):
        session_factory, _ = temp_db
        service = QuizService(
            quiz_repository=QuizRepository(session_factory=session_factory),
            progress_repository=ProgressRepository(session_factory=session_factory),
            session_factory=session_factory,
        )
        with pytest.raises(HTTPException) as exc:
            service.update_question(
                question_id=9999, payload=QuestionUpdate(statement="X"), instructor_id=1
            )
        assert exc.value.status_code == 404

    def test_delete_question_hard_delete_when_unanswered(self, temp_db):
        session_factory, _ = temp_db
        quiz_repo = QuizRepository(session_factory=session_factory)
        prog_repo = ProgressRepository(session_factory=session_factory)
        prog_repo.set_course_owner(course_id=1, instructor_id=1)
        service = QuizService(
            quiz_repository=quiz_repo,
            progress_repository=prog_repo,
            session_factory=session_factory,
        )

        created = service.create_question(
            course_id=1,
            payload=QuestionCreate(
                statement="To be deleted",
                options=["A", "B"],
                correct_option_index=0,
                difficulty="Easy",
            ),
            instructor_id=1,
        )

        result = service.delete_question(question_id=created.id, instructor_id=1)
        assert result["soft_deleted"] is False
        assert result["deleted"] is True
        assert quiz_repo.get_question_by_id(created.id) is None

    def test_delete_question_soft_delete_when_answered(self, temp_db):
        session_factory, _ = temp_db
        quiz_repo = QuizRepository(session_factory=session_factory)
        prog_repo = ProgressRepository(session_factory=session_factory)
        prog_repo.set_course_owner(course_id=1, instructor_id=1)
        service = QuizService(
            quiz_repository=quiz_repo,
            progress_repository=prog_repo,
            session_factory=session_factory,
        )

        created = service.create_question(
            course_id=1,
            payload=QuestionCreate(
                statement="Answered item",
                options=["A", "B"],
                correct_option_index=1,
                difficulty="Medium",
            ),
            instructor_id=1,
        )

        quiz_repo.record_attempt_answers(
            [
                AnswerRecordInput(
                    attempt_id=1,
                    question_id=created.id,
                    selected_option_index=1,
                    is_correct=True,
                    topic_id=1,
                    difficulty_at_attempt="Medium",
                )
            ]
        )

        result = service.delete_question(question_id=created.id, instructor_id=1)
        assert result["soft_deleted"] is True
        assert result["is_active"] is False

        loaded = quiz_repo.get_question_by_id(created.id)
        assert loaded is not None
        assert loaded.is_active is False


class TestQuizServiceQuizManagement:
    """Test quiz authoring, publishing, and presentation views (FR-10, FR-11, FR-12)."""

    def test_create_and_publish_quiz(self, temp_db):
        session_factory, _ = temp_db
        quiz_repo = QuizRepository(session_factory=session_factory)
        prog_repo = ProgressRepository(session_factory=session_factory)
        prog_repo.set_course_owner(course_id=1, instructor_id=1)
        service = QuizService(
            quiz_repository=quiz_repo,
            progress_repository=prog_repo,
            session_factory=session_factory,
        )

        q1 = service.create_question(
            course_id=1,
            payload=QuestionCreate(
                statement="Q1", options=["A", "B"], correct_option_index=0, difficulty="Easy"
            ),
            instructor_id=1,
        )

        quiz = service.create_quiz(
            course_id=1,
            payload=QuizCreate(title="Midterm Quiz", question_ids=[q1.id], is_published=False),
            instructor_id=1,
        )
        assert quiz.id is not None
        assert quiz.is_published is False
        assert len(quiz.questions) == 1

        published = service.publish_quiz(quiz.id, is_published=True, instructor_id=1)
        assert published.is_published is True

    def test_publish_empty_quiz_rejected(self, temp_db):
        """Publishing a quiz with zero questions is defensively rejected (FR-10)."""
        session_factory, _ = temp_db
        quiz_repo = QuizRepository(session_factory=session_factory)
        prog_repo = ProgressRepository(session_factory=session_factory)
        prog_repo.set_course_owner(course_id=1, instructor_id=1)
        service = QuizService(
            quiz_repository=quiz_repo,
            progress_repository=prog_repo,
            session_factory=session_factory,
        )

        empty_quiz = service.create_quiz(
            course_id=1,
            payload=QuizCreate(title="Empty Quiz", question_ids=[], is_published=False),
            instructor_id=1,
        )
        with pytest.raises(HTTPException) as exc:
            service.publish_quiz(empty_quiz.id, is_published=True, instructor_id=1)
        assert exc.value.status_code == 400
        assert "Cannot publish a quiz with zero questions" in exc.value.detail

    def test_get_quiz_for_taking_student_safe_strips_answers(self, temp_db):
        """Student-safe view strips correct_option_index and explanation (FR-11)."""
        session_factory, _ = temp_db
        quiz_repo = QuizRepository(session_factory=session_factory)
        prog_repo = ProgressRepository(session_factory=session_factory)
        prog_repo.set_course_owner(course_id=1, instructor_id=1)
        prog_repo.enroll_student(student_id=101, course_id=1)
        service = QuizService(
            quiz_repository=quiz_repo,
            progress_repository=prog_repo,
            session_factory=session_factory,
        )

        q1 = service.create_question(
            course_id=1,
            payload=QuestionCreate(
                statement="Secret Answer Question",
                options=["Choice A", "Choice B"],
                correct_option_index=1,
                difficulty="Medium",
                explanation="Confidential teacher explanation",
            ),
            instructor_id=1,
        )
        quiz = service.create_quiz(
            course_id=1,
            payload=QuizCreate(title="Live Exam", question_ids=[q1.id], is_published=True),
            instructor_id=1,
        )

        safe = service.get_quiz_for_taking(quiz.id, student_id=101)
        assert safe.id == quiz.id
        assert len(safe.questions) == 1
        q_dict = safe.questions[0].model_dump()
        assert "correct_option_index" not in q_dict
        assert "explanation" not in q_dict
        assert q_dict["statement"] == "Secret Answer Question"
        assert q_dict["options"] == ["Choice A", "Choice B"]

    def test_get_quiz_for_taking_unenrolled_student_rejected(self, temp_db):
        """Unenrolled student cannot retrieve quiz (NFR-05)."""
        session_factory, _ = temp_db
        quiz_repo = QuizRepository(session_factory=session_factory)
        prog_repo = ProgressRepository(session_factory=session_factory)
        prog_repo.set_course_owner(course_id=1, instructor_id=1)
        service = QuizService(
            quiz_repository=quiz_repo,
            progress_repository=prog_repo,
            session_factory=session_factory,
        )

        quiz = service.create_quiz(
            course_id=1,
            payload=QuizCreate(title="Exam", is_published=True),
            instructor_id=1,
        )
        with pytest.raises(HTTPException) as exc:
            service.get_quiz_for_taking(quiz.id, student_id=999)  # Student 999 not enrolled
        assert exc.value.status_code == 403
        assert "not enrolled in course" in exc.value.detail

    def test_create_practice_quiz_success(self, temp_db):
        """Assembles on-demand practice quiz from active topic questions (FR-12)."""
        session_factory, _ = temp_db
        quiz_repo = QuizRepository(session_factory=session_factory)
        prog_repo = ProgressRepository(session_factory=session_factory)
        prog_repo.enroll_student(student_id=101, course_id=1)
        service = QuizService(
            quiz_repository=quiz_repo,
            progress_repository=prog_repo,
            session_factory=session_factory,
        )

        prog_repo.set_course_owner(course_id=1, instructor_id=1)
        for i in range(4):
            service.create_question(
                course_id=1,
                payload=QuestionCreate(
                    statement=f"Q{i}", options=["A", "B"], correct_option_index=0, difficulty="Easy"
                ),
                instructor_id=1,
                topic_id=7,
            )

        practice = service.create_practice_quiz(
            course_id=1,
            payload=PracticeQuizRequest(topic_id=7, question_count=3),
            student_id=101,
        )
        assert practice.id is not None
        assert len(practice.questions) == 3
        assert "Practice Quiz: Topic 7" in practice.title


class TestQuizServiceSubmissionAndGrading:
    """Test automated grading, score breakdown, and atomic transaction (FR-13, FR-14, NFR-08)."""

    def test_submit_quiz_attempt_scoring_and_atomic_persistence(self, temp_db):
        """Submits attempt, grades answers, updates question stats, and commits atomically (FR-13, NFR-08)."""
        session_factory, _engine = temp_db
        quiz_repo = QuizRepository(session_factory=session_factory)
        prog_repo = ProgressRepository(session_factory=session_factory)
        adapt_repo = AdaptiveRepository(session_factory=session_factory)

        prog_repo.set_course_owner(course_id=1, instructor_id=1)
        prog_repo.enroll_student(student_id=101, course_id=1)
        service = QuizService(
            quiz_repository=quiz_repo,
            progress_repository=prog_repo,
            adaptive_repository=adapt_repo,
            session_factory=session_factory,
        )

        q1 = service.create_question(
            course_id=1,
            payload=QuestionCreate(
                statement="Q1", options=["A", "B"], correct_option_index=0, difficulty="Easy"
            ),
            instructor_id=1,
            topic_id=1,
        )
        q2 = service.create_question(
            course_id=1,
            payload=QuestionCreate(
                statement="Q2", options=["C", "D"], correct_option_index=1, difficulty="Hard"
            ),
            instructor_id=1,
            topic_id=2,
        )
        quiz = service.create_quiz(
            course_id=1,
            payload=QuizCreate(title="Graded Exam", question_ids=[q1.id, q2.id], is_published=True),
            instructor_id=1,
        )

        # Student submits: q1 correct (0), q2 incorrect (0)
        submission = QuizAttemptSubmitRequest(
            answers=[
                AnswerSubmissionItem(question_id=q1.id, selected_option_index=0),
                AnswerSubmissionItem(question_id=q2.id, selected_option_index=0),
            ]
        )
        result = service.submit_quiz_attempt(quiz.id, student_id=101, payload=submission)

        assert result.attempt_id is not None
        assert result.score == 0.5  # 1 out of 2 correct
        assert result.total_questions == 2
        assert result.correct_answers == 1
        assert len(result.topic_scores) == 2
        assert len(result.answers) == 2
        assert result.answers[0].is_correct is True
        assert result.answers[1].is_correct is False

        # Verify atomic database persistence
        with session_factory() as session:
            # Check attempt in quiz_attempts
            attempt_row = (
                session.query(AttemptModel).filter_by(attempt_id=result.attempt_id).first()
            )
            assert attempt_row is not None
            assert attempt_row.score == 0.5
            assert attempt_row.student_id == 101

            # Check individual answers in attempt_answers
            answers_rows = (
                session.query(AttemptAnswerModel).filter_by(attempt_id=result.attempt_id).all()
            )
            assert len(answers_rows) == 2

            # Check question stats in course_question_stats (FR-24)
            q1_stat = session.query(QuestionStatsModel).filter_by(question_id=q1.id).first()
            assert q1_stat is not None
            assert q1_stat.times_answered == 1
            assert q1_stat.correct_count == 1

            q2_stat = session.query(QuestionStatsModel).filter_by(question_id=q2.id).first()
            assert q2_stat is not None
            assert q2_stat.times_answered == 1
            assert q2_stat.correct_count == 0

            # Check adaptive topic responses for M3 (FR-16)
            topic_responses = (
                session.query(StudentTopicResponseModel).filter_by(student_id=101).all()
            )
            assert len(topic_responses) == 2

    def test_submit_quiz_attempt_invalid_question_id_rejected(self, temp_db):
        """Submitting answer to a question not in the quiz raises 400 Bad Request."""
        session_factory, _ = temp_db
        quiz_repo = QuizRepository(session_factory=session_factory)
        prog_repo = ProgressRepository(session_factory=session_factory)
        prog_repo.set_course_owner(course_id=1, instructor_id=1)
        prog_repo.enroll_student(student_id=101, course_id=1)
        service = QuizService(
            quiz_repository=quiz_repo,
            progress_repository=prog_repo,
            session_factory=session_factory,
        )

        q1 = service.create_question(
            course_id=1,
            payload=QuestionCreate(
                statement="Q1", options=["A", "B"], correct_option_index=0, difficulty="Easy"
            ),
            instructor_id=1,
        )
        quiz = service.create_quiz(
            course_id=1,
            payload=QuizCreate(title="Exam", question_ids=[q1.id], is_published=True),
            instructor_id=1,
        )

        with pytest.raises(HTTPException) as exc:
            service.submit_quiz_attempt(
                quiz.id,
                student_id=101,
                payload=QuizAttemptSubmitRequest(
                    answers=[AnswerSubmissionItem(question_id=999, selected_option_index=0)]
                ),
            )
        assert exc.value.status_code == 400
        assert "does not belong to quiz" in exc.value.detail

    def test_get_attempt_result_privacy_enforcement(self, temp_db):
        """Cross-student viewing of attempt results is rejected with 403 Forbidden (NFR-06)."""
        session_factory, _ = temp_db
        quiz_repo = QuizRepository(session_factory=session_factory)
        prog_repo = ProgressRepository(session_factory=session_factory)
        prog_repo.set_course_owner(course_id=1, instructor_id=1)
        prog_repo.enroll_student(student_id=101, course_id=1)
        prog_repo.enroll_student(student_id=102, course_id=1)
        service = QuizService(
            quiz_repository=quiz_repo,
            progress_repository=prog_repo,
            session_factory=session_factory,
        )

        q1 = service.create_question(
            course_id=1,
            payload=QuestionCreate(
                statement="Q1", options=["A", "B"], correct_option_index=0, difficulty="Easy"
            ),
            instructor_id=1,
        )
        quiz = service.create_quiz(
            course_id=1,
            payload=QuizCreate(title="Exam", question_ids=[q1.id], is_published=True),
            instructor_id=1,
        )

        result = service.submit_quiz_attempt(
            quiz.id,
            student_id=101,
            payload=QuizAttemptSubmitRequest(
                answers=[AnswerSubmissionItem(question_id=q1.id, selected_option_index=0)]
            ),
        )

        # Attempt owner (Student 101) can view
        owner_view = service.get_attempt_result(result.attempt_id, user_id=101, role="student")
        assert owner_view.attempt_id == result.attempt_id

        # Course instructor (Instructor 1) can view
        instructor_view = service.get_attempt_result(
            result.attempt_id, user_id=1, role="instructor"
        )
        assert instructor_view.attempt_id == result.attempt_id

        # Another student (Student 102) is forbidden
        with pytest.raises(HTTPException) as exc:
            service.get_attempt_result(result.attempt_id, user_id=102, role="student")
        assert exc.value.status_code == 403
        assert "Access denied" in exc.value.detail
