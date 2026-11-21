"""White-box Basis Path Testing for Quiz Scoring & Evaluation Engine.

Course Compliance:
- SE423: Defensive programming, robust scoring calculation, transaction atomicity.
- SE431: White-box testing, Basis Path Testing (McCabe cyclomatic complexity),
        Statement & Branch coverage, Boundary Value Analysis.

Cyclomatic Complexity Analysis for `QuizService.submit_quiz_attempt`:
---------------------------------------------------------------------
Control Flow Graph (CFG) Decision Points:
1. Decision D1: `if quiz is None` (raises HTTP 404)
2. Decision D2: `if not quiz.is_published` (raises HTTP 400)
3. Decision D3: `if not is_student_enrolled` (raises HTTP 403)
4. Decision D4: `if not quiz_question_map` (raises HTTP 400)
5. For each submitted answer:
   - Decision D5: `if item.question_id in seen_question_ids` (duplicate detection, raises HTTP 400)
   - Decision D6: `if item.question_id not in quiz_question_map` (foreign question, raises HTTP 400)
   - Decision D7: `if not (0 <= item.selected_option_index < len(q.options))` (raises HTTP 422)
   - Decision D8: `is_correct = (item.selected_option_index == q.correct_option_index)` (Branch True vs False)
6. Decision D9: Database transaction failure handling (try ... except rollback)

Basis Paths:
- Basis Path 1 (All-Correct Complete Evaluation):
  All submitted answers valid & correct. Score = 1.0, 100% accuracy across topics.
- Basis Path 2 (All-Incorrect Complete Evaluation):
  All submitted answers valid & incorrect. Score = 0.0, 0% accuracy across topics.
- Basis Path 3 (Mixed & Multi-Topic Aggregation with Precision):
  Answers alternate True/False across multiple distinct topics; verifies independent topic breakdown and 4-decimal precision.
- Basis Path 4 (Partial / Unanswered Submission Handling):
  Student submits answers for subset M < N. Unanswered questions receive 0 credit; denominator remains total quiz questions.
"""
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

# Ensure backend package is on sys.path
backend_root = Path(__file__).resolve().parents[2]
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from fastapi import HTTPException
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import init_db
from app.models.adaptive import StudentTopicResponseModel
from app.models.progress import AttemptModel, CourseOwnerModel, EnrollmentModel, QuestionStatsModel
from app.models.quiz import AttemptAnswerModel
from app.repositories.adaptive_repository import AdaptiveRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.quiz_repository import QuizRepository
from app.schemas.quiz import (
    AnswerSubmissionItem,
    QuestionCreate,
    QuizAttemptSubmitRequest,
    QuizCreate,
)
from app.services.quiz_service import QuizService


@pytest.fixture
def scoring_env():
    """Set up an isolated database and QuizService environment populated with course and test data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    init_db(target_engine=engine)

    quiz_repo = QuizRepository(session_factory=session_factory)
    progress_repo = ProgressRepository(session_factory=session_factory)
    adaptive_repo = AdaptiveRepository(session_factory=session_factory)
    service = QuizService(
        quiz_repository=quiz_repo,
        progress_repository=progress_repo,
        adaptive_repository=adaptive_repo,
        session_factory=session_factory,
    )

    # Seed baseline course ownership and enrollment
    with session_factory() as session:
        session.add(CourseOwnerModel(course_id=1, instructor_id=10))
        session.add(EnrollmentModel(course_id=1, student_id=101))
        session.add(EnrollmentModel(course_id=1, student_id=102))
        session.commit()

    yield {
        "service": service,
        "quiz_repo": quiz_repo,
        "session_factory": session_factory,
        "course_id": 1,
        "instructor_id": 10,
        "student_id": 101,
        "unenrolled_student_id": 999,
    }

    engine.dispose()
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError:
            pass


class TestBasisPathScoring:
    """White-box basis path execution suite for assessment scoring."""

    def test_basis_path_1_all_correct_scoring(self, scoring_env):
        """Basis Path 1: All submitted answers are valid and correct (100% score)."""
        service: QuizService = scoring_env["service"]
        cid = scoring_env["course_id"]
        iid = scoring_env["instructor_id"]
        sid = scoring_env["student_id"]

        # Create 3 questions across 2 topics (T10 has 2, T20 has 1)
        q1 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Topic 10 Q1",
                options=["A", "B", "C"], correct_option_index=0, difficulty="easy",
            ),
            instructor_id=iid,
            topic_id=10,
        )
        q2 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Topic 10 Q2",
                options=["X", "Y", "Z"], correct_option_index=1, difficulty="medium",
            ),
            instructor_id=iid,
            topic_id=10,
        )
        q3 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=20, statement="Topic 20 Q1",
                options=["1", "2", "3", "4"], correct_option_index=2, difficulty="hard",
            ),
            instructor_id=iid,
            topic_id=20,
        )

        quiz = service.create_quiz(
            course_id=cid,
            payload=QuizCreate(
                course_id=cid, title="Full Mastery Quiz", question_ids=[q1.id, q2.id, q3.id]
            ),
            instructor_id=iid,
        )
        service.publish_quiz(quiz.id, is_published=True, instructor_id=iid)

        # Submit attempt with all correct choices
        submission = QuizAttemptSubmitRequest(answers=[
            AnswerSubmissionItem(question_id=q1.id, selected_option_index=0),
            AnswerSubmissionItem(question_id=q2.id, selected_option_index=1),
            AnswerSubmissionItem(question_id=q3.id, selected_option_index=2),
        ])
        result = service.submit_quiz_attempt(quiz.id, sid, submission)

        assert result.total_questions == 3
        assert result.correct_answers == 3
        assert result.score == 1.0  # 3 / 3
        assert all(a.is_correct is True for a in result.answers)

        # Topic breakdowns
        topic_map = {tb.topic_id: tb for tb in result.topic_scores}
        assert topic_map[10].correct_count == 2
        assert topic_map[10].total_questions == 2
        assert topic_map[10].topic_score == 1.0

        assert topic_map[20].correct_count == 1
        assert topic_map[20].total_questions == 1
        assert topic_map[20].topic_score == 1.0

    def test_basis_path_2_all_incorrect_scoring(self, scoring_env):
        """Basis Path 2: All submitted answers are valid and incorrect (0% score)."""
        service: QuizService = scoring_env["service"]
        cid = scoring_env["course_id"]
        iid = scoring_env["instructor_id"]
        sid = scoring_env["student_id"]

        q1 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Topic 10 Q1",
                options=["A", "B", "C"], correct_option_index=0, difficulty="easy",
            ),
            instructor_id=iid,
            topic_id=10,
        )
        q2 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Topic 10 Q2",
                options=["X", "Y", "Z"], correct_option_index=1, difficulty="medium",
            ),
            instructor_id=iid,
            topic_id=10,
        )

        quiz = service.create_quiz(
            course_id=cid,
            payload=QuizCreate(
                course_id=cid, title="Zero Score Quiz", question_ids=[q1.id, q2.id]
            ),
            instructor_id=iid,
        )
        service.publish_quiz(quiz.id, is_published=True, instructor_id=iid)

        # Submit deliberately incorrect answers
        submission = QuizAttemptSubmitRequest(answers=[
            AnswerSubmissionItem(question_id=q1.id, selected_option_index=1),
            AnswerSubmissionItem(question_id=q2.id, selected_option_index=2),
        ])
        result = service.submit_quiz_attempt(quiz.id, sid, submission)

        assert result.total_questions == 2
        assert result.correct_answers == 0
        assert result.score == 0.0
        assert all(a.is_correct is False for a in result.answers)

        topic_map = {tb.topic_id: tb for tb in result.topic_scores}
        assert topic_map[10].correct_count == 0
        assert topic_map[10].total_questions == 2
        assert topic_map[10].topic_score == 0.0

    def test_basis_path_3_mixed_and_precision_scoring(self, scoring_env):
        """Basis Path 3: Alternating correct/incorrect across multi-topic quiz with precision check."""
        service: QuizService = scoring_env["service"]
        cid = scoring_env["course_id"]
        iid = scoring_env["instructor_id"]
        sid = scoring_env["student_id"]

        # 4 questions: T10 has 2 questions, T20 has 2 questions
        q1 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Q1",
                options=["A", "B"], correct_option_index=0, difficulty="easy",
            ),
            instructor_id=iid,
            topic_id=10,
        )
        q2 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Q2",
                options=["A", "B"], correct_option_index=0, difficulty="easy",
            ),
            instructor_id=iid,
            topic_id=10,
        )
        q3 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=20, statement="Q3",
                options=["A", "B"], correct_option_index=0, difficulty="medium",
            ),
            instructor_id=iid,
            topic_id=20,
        )
        q4 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=20, statement="Q4",
                options=["A", "B"], correct_option_index=0, difficulty="medium",
            ),
            instructor_id=iid,
            topic_id=20,
        )

        quiz = service.create_quiz(
            course_id=cid,
            payload=QuizCreate(
                course_id=cid, title="Mixed Multi-Topic Quiz", question_ids=[q1.id, q2.id, q3.id, q4.id]
            ),
            instructor_id=iid,
        )
        service.publish_quiz(quiz.id, is_published=True, instructor_id=iid)

        # Student gets:
        # q1: correct (1/2 in T10)
        # q2: incorrect
        # q3: correct (2/2 in T20)
        # q4: correct
        # Overall: 3 / 4 = 0.75 (75.0%)
        submission = QuizAttemptSubmitRequest(answers=[
            AnswerSubmissionItem(question_id=q1.id, selected_option_index=0),
            AnswerSubmissionItem(question_id=q2.id, selected_option_index=1),
            AnswerSubmissionItem(question_id=q3.id, selected_option_index=0),
            AnswerSubmissionItem(question_id=q4.id, selected_option_index=0),
        ])
        result = service.submit_quiz_attempt(quiz.id, sid, submission)

        assert result.total_questions == 4
        assert result.correct_answers == 3
        assert result.score == 0.75

        topic_map = {tb.topic_id: tb for tb in result.topic_scores}
        assert topic_map[10].correct_count == 1
        assert topic_map[10].total_questions == 2
        assert topic_map[10].topic_score == 0.5

        assert topic_map[20].correct_count == 2
        assert topic_map[20].total_questions == 2
        assert topic_map[20].topic_score == 1.0

    def test_basis_path_4_partial_unanswered_questions_scoring(self, scoring_env):
        """Basis Path 4: Partial submission where student answers only a subset of questions.
        
        Denominator must remain total quiz questions; unanswered questions receive 0 credit.
        """
        service: QuizService = scoring_env["service"]
        cid = scoring_env["course_id"]
        iid = scoring_env["instructor_id"]
        sid = scoring_env["student_id"]

        # Quiz with 3 questions
        q1 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Q1",
                options=["A", "B"], correct_option_index=0, difficulty="easy",
            ),
            instructor_id=iid,
            topic_id=10,
        )
        q2 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Q2",
                options=["A", "B"], correct_option_index=0, difficulty="easy",
            ),
            instructor_id=iid,
            topic_id=10,
        )
        q3 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Q3",
                options=["A", "B"], correct_option_index=0, difficulty="easy",
            ),
            instructor_id=iid,
            topic_id=10,
        )

        quiz = service.create_quiz(
            course_id=cid,
            payload=QuizCreate(
                course_id=cid, title="Partial Submission Quiz", question_ids=[q1.id, q2.id, q3.id]
            ),
            instructor_id=iid,
        )
        service.publish_quiz(quiz.id, is_published=True, instructor_id=iid)

        # Student submits answers for only 2 of the 3 questions: q1 correct, q2 incorrect, q3 omitted
        submission = QuizAttemptSubmitRequest(answers=[
            AnswerSubmissionItem(question_id=q1.id, selected_option_index=0),
            AnswerSubmissionItem(question_id=q2.id, selected_option_index=1),
        ])
        result = service.submit_quiz_attempt(quiz.id, sid, submission)

        assert result.total_questions == 3
        assert result.correct_answers == 1
        # 1 / 3 rounded to 4 decimals = 0.3333
        assert result.score == 0.3333
        assert len(result.answers) == 2


class TestScoringBoundaryAndDefensivePaths:
    """Boundary value analysis and defensive error paths for quiz scoring."""

    def test_duplicate_question_id_in_submission_rejected(self, scoring_env):
        """Decision D5: Duplicate submission for the same question ID must be rejected (HTTP 400)."""
        service: QuizService = scoring_env["service"]
        cid = scoring_env["course_id"]
        iid = scoring_env["instructor_id"]
        sid = scoring_env["student_id"]

        q1 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Q1",
                options=["A", "B"], correct_option_index=0, difficulty="easy",
            ),
            instructor_id=iid,
            topic_id=10,
        )
        quiz = service.create_quiz(
            course_id=cid,
            payload=QuizCreate(
                course_id=cid, title="Single Question Quiz", question_ids=[q1.id]
            ),
            instructor_id=iid,
        )
        service.publish_quiz(quiz.id, is_published=True, instructor_id=iid)

        # Submitting q1 twice
        submission = QuizAttemptSubmitRequest(answers=[
            AnswerSubmissionItem(question_id=q1.id, selected_option_index=0),
            AnswerSubmissionItem(question_id=q1.id, selected_option_index=0),
        ])

        with pytest.raises(HTTPException) as exc_info:
            service.submit_quiz_attempt(quiz.id, sid, submission)
        assert exc_info.value.status_code == 400
        assert "duplicate" in exc_info.value.detail.lower()

    def test_foreign_question_id_rejected(self, scoring_env):
        """Decision D6: Submitting answer for a question not in the quiz is rejected (HTTP 400)."""
        service: QuizService = scoring_env["service"]
        cid = scoring_env["course_id"]
        iid = scoring_env["instructor_id"]
        sid = scoring_env["student_id"]

        q1 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Q1",
                options=["A", "B"], correct_option_index=0, difficulty="easy",
            ),
            instructor_id=iid,
            topic_id=10,
        )
        q_foreign = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Foreign Q",
                options=["A", "B"], correct_option_index=0, difficulty="easy",
            ),
            instructor_id=iid,
            topic_id=10,
        )

        quiz = service.create_quiz(
            course_id=cid,
            payload=QuizCreate(
                course_id=cid, title="Strict Membership Quiz", question_ids=[q1.id]
            ),
            instructor_id=iid,
        )
        service.publish_quiz(quiz.id, is_published=True, instructor_id=iid)

        submission = QuizAttemptSubmitRequest(answers=[
            AnswerSubmissionItem(question_id=q_foreign.id, selected_option_index=0),
        ])

        with pytest.raises(HTTPException) as exc_info:
            service.submit_quiz_attempt(quiz.id, sid, submission)
        assert exc_info.value.status_code == 400
        assert "does not belong" in exc_info.value.detail

    def test_out_of_bounds_option_index_rejected(self, scoring_env):
        """Decision D7: Selected option index beyond option count must be rejected (HTTP 422)."""
        service: QuizService = scoring_env["service"]
        cid = scoring_env["course_id"]
        iid = scoring_env["instructor_id"]
        sid = scoring_env["student_id"]

        q1 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Q1",
                options=["A", "B"], correct_option_index=0, difficulty="easy",
            ),
            instructor_id=iid,
            topic_id=10,
        )
        quiz = service.create_quiz(
            course_id=cid,
            payload=QuizCreate(
                course_id=cid, title="Option Bounds Quiz", question_ids=[q1.id]
            ),
            instructor_id=iid,
        )
        service.publish_quiz(quiz.id, is_published=True, instructor_id=iid)

        # Index 5 on a 2-option question
        submission = QuizAttemptSubmitRequest(answers=[
            AnswerSubmissionItem(question_id=q1.id, selected_option_index=5),
        ])

        with pytest.raises(HTTPException) as exc_info:
            service.submit_quiz_attempt(quiz.id, sid, submission)
        assert exc_info.value.status_code == 422
        assert "out of bounds" in exc_info.value.detail

    def test_unpublished_quiz_submission_rejected(self, scoring_env):
        """Decision D2: Attempt on an unpublished quiz must be rejected (HTTP 400)."""
        service: QuizService = scoring_env["service"]
        cid = scoring_env["course_id"]
        iid = scoring_env["instructor_id"]
        sid = scoring_env["student_id"]

        q1 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Q1",
                options=["A", "B"], correct_option_index=0, difficulty="easy",
            ),
            instructor_id=iid,
            topic_id=10,
        )
        quiz = service.create_quiz(
            course_id=cid,
            payload=QuizCreate(
                course_id=cid, title="Draft Quiz", question_ids=[q1.id]
            ),
            instructor_id=iid,
        )
        # Do not publish

        submission = QuizAttemptSubmitRequest(answers=[
            AnswerSubmissionItem(question_id=q1.id, selected_option_index=0),
        ])

        with pytest.raises(HTTPException) as exc_info:
            service.submit_quiz_attempt(quiz.id, sid, submission)
        assert exc_info.value.status_code == 400
        assert "unpublished" in exc_info.value.detail.lower()

    def test_nonexistent_quiz_submission_rejected(self, scoring_env):
        """Decision D1: Non-existent quiz ID must return HTTP 404."""
        service: QuizService = scoring_env["service"]
        sid = scoring_env["student_id"]

        submission = QuizAttemptSubmitRequest(answers=[
            AnswerSubmissionItem(question_id=1, selected_option_index=0),
        ])

        with pytest.raises(HTTPException) as exc_info:
            service.submit_quiz_attempt(9999, sid, submission)
        assert exc_info.value.status_code == 404

    def test_unenrolled_student_submission_rejected(self, scoring_env):
        """Decision D3: Unenrolled student must be rejected with HTTP 403."""
        service: QuizService = scoring_env["service"]
        cid = scoring_env["course_id"]
        iid = scoring_env["instructor_id"]
        unenrolled_sid = scoring_env["unenrolled_student_id"]

        q1 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Q1",
                options=["A", "B"], correct_option_index=0, difficulty="easy",
            ),
            instructor_id=iid,
            topic_id=10,
        )
        quiz = service.create_quiz(
            course_id=cid,
            payload=QuizCreate(
                course_id=cid, title="Enrolled Only Quiz", question_ids=[q1.id]
            ),
            instructor_id=iid,
        )
        service.publish_quiz(quiz.id, is_published=True, instructor_id=iid)

        submission = QuizAttemptSubmitRequest(answers=[
            AnswerSubmissionItem(question_id=q1.id, selected_option_index=0),
        ])

        with pytest.raises(HTTPException) as exc_info:
            service.submit_quiz_attempt(quiz.id, unenrolled_sid, submission)
        assert exc_info.value.status_code == 403

    def test_atomic_transaction_rollback_on_persistence_error(self, scoring_env):
        """Decision D9: If any part of persistence fails, entire transaction rolls back."""
        service: QuizService = scoring_env["service"]
        session_factory = scoring_env["session_factory"]
        cid = scoring_env["course_id"]
        iid = scoring_env["instructor_id"]
        sid = scoring_env["student_id"]

        q1 = service.create_question(
            course_id=cid,
            payload=QuestionCreate(
                course_id=cid, topic_id=10, statement="Q1",
                options=["A", "B"], correct_option_index=0, difficulty="easy",
            ),
            instructor_id=iid,
            topic_id=10,
        )
        quiz = service.create_quiz(
            course_id=cid,
            payload=QuizCreate(
                course_id=cid, title="Rollback Quiz", question_ids=[q1.id]
            ),
            instructor_id=iid,
        )
        service.publish_quiz(quiz.id, is_published=True, instructor_id=iid)

        submission = QuizAttemptSubmitRequest(answers=[
            AnswerSubmissionItem(question_id=q1.id, selected_option_index=0),
        ])

        # Patch Session.commit inside submit_quiz_attempt to raise an exception
        with patch("sqlalchemy.orm.Session.commit", side_effect=RuntimeError("Simulated Disk/Commit Failure")):
            with pytest.raises(HTTPException) as exc_info:
                service.submit_quiz_attempt(quiz.id, sid, submission)
            assert exc_info.value.status_code == 500
            assert "transaction failed" in exc_info.value.detail.lower()

        # Verify that zero records were committed
        with session_factory() as session:
            attempts = session.query(AttemptModel).filter_by(quiz_id=quiz.id).all()
            answers = session.query(AttemptAnswerModel).filter_by(question_id=q1.id).all()
            adaptive_responses = session.query(StudentTopicResponseModel).filter_by(student_id=sid).all()

            assert len(attempts) == 0
            assert len(answers) == 0
            assert len(adaptive_responses) == 0
