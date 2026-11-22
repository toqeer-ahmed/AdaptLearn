"""Unit and persistence tests for Module 2: Quiz & Assessment Engine repository and models.

Requirements Traceability:
- FR-08: MCQ question bank management (fields, options, correct index, difficulty).
- FR-09: Soft-deletion of answered questions (is_active = False if attempt answers exist).
- FR-10: Quiz creation, question association, ordering, and publishing.
- FR-11: Quiz retrieval and question bank querying.
- FR-12: Active question retrieval for topic practice quizzes.
- NFR-07 & NFR-08: Transactional integrity and persistence across repository restart.
- NFR-09: Referential integrity and relational constraints.
- Decision D2 & D3: JSON array options, single correct option index, quiz_questions join table.
"""

import contextlib
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import init_db
from app.repositories.quiz_repository import (
    AnswerRecordInput,
    QuestionRecordInput,
    QuizRecordInput,
    QuizRepository,
)


@pytest.fixture
def temp_db():
    """Create an isolated temporary SQLite database file for persistence testing."""
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


class TestQuizRepositoryQuestionManagement:
    """Test QuestionModel persistence, CRUD, and soft-delete semantics (FR-08, FR-09)."""

    def test_question_creation_and_restart_survival(self, temp_db):
        """Question persists with JSON options and survives repository instance recreation."""
        session_factory, _ = temp_db

        repo_1 = QuizRepository(session_factory=session_factory)
        question_input = QuestionRecordInput(
            course_id=1,
            topic_id=10,
            statement="What does boundary value analysis test?",
            options=[
                "Center values",
                "Minimum and maximum edges",
                "Random inputs",
                "Only negative numbers",
            ],
            correct_option_index=1,
            difficulty="Medium",
            explanation="BVA focuses on the boundaries of input domains.",
        )
        created = repo_1.create_question(question_input)
        assert created.id is not None
        assert created.statement == "What does boundary value analysis test?"
        assert created.options == [
            "Center values",
            "Minimum and maximum edges",
            "Random inputs",
            "Only negative numbers",
        ]
        assert created.correct_option_index == 1
        assert created.difficulty == "Medium"
        assert created.is_active is True

        # Simulate process termination / restart by destroying repo_1
        del repo_1
        repo_2 = QuizRepository(session_factory=session_factory)

        loaded = repo_2.get_question_by_id(created.id)
        assert loaded is not None
        assert loaded.id == created.id
        assert loaded.course_id == 1
        assert loaded.topic_id == 10
        assert loaded.statement == "What does boundary value analysis test?"
        assert loaded.options == [
            "Center values",
            "Minimum and maximum edges",
            "Random inputs",
            "Only negative numbers",
        ]
        assert loaded.correct_option_index == 1
        assert loaded.difficulty == "Medium"
        assert loaded.explanation == "BVA focuses on the boundaries of input domains."
        assert loaded.is_active is True

    def test_question_update(self, temp_db):
        """Updating question attributes persists correctly."""
        session_factory, _ = temp_db
        repo = QuizRepository(session_factory=session_factory)

        created = repo.create_question(
            QuestionRecordInput(
                course_id=1,
                topic_id=5,
                statement="Original statement",
                options=["A", "B"],
                correct_option_index=0,
                difficulty="Easy",
            )
        )

        updated = repo.update_question(
            question_id=created.id,
            statement="Updated statement",
            options=["A", "B", "C"],
            correct_option_index=2,
            difficulty="Hard",
            explanation="Updated explanation",
        )
        assert updated is not None
        assert updated.statement == "Updated statement"
        assert len(updated.options) == 3
        assert updated.correct_option_index == 2
        assert updated.difficulty == "Hard"
        assert updated.explanation == "Updated explanation"

        # Verify reload
        reloaded = repo.get_question_by_id(created.id)
        assert reloaded.statement == "Updated statement"
        assert reloaded.difficulty == "Hard"

    def test_question_hard_delete_when_unanswered(self, temp_db):
        """An unattempted question is physically removed from the database (FR-09)."""
        session_factory, _ = temp_db
        repo = QuizRepository(session_factory=session_factory)

        created = repo.create_question(
            QuestionRecordInput(
                course_id=1,
                topic_id=3,
                statement="Unanswered question",
                options=["Yes", "No"],
                correct_option_index=0,
                difficulty="Easy",
            )
        )

        was_soft_deleted = repo.delete_question(created.id)
        assert was_soft_deleted is False  # False indicates hard delete

        assert repo.get_question_by_id(created.id) is None

    def test_question_soft_delete_when_answered(self, temp_db):
        """A question with historical attempt answers is soft-deleted (is_active = False) (FR-09)."""
        session_factory, _ = temp_db
        repo = QuizRepository(session_factory=session_factory)

        created = repo.create_question(
            QuestionRecordInput(
                course_id=1,
                topic_id=4,
                statement="Answered question that must not be deleted",
                options=["Opt 1", "Opt 2"],
                correct_option_index=1,
                difficulty="Medium",
            )
        )

        # Simulate student attempt answer referencing this question
        repo.record_attempt_answers(
            [
                AnswerRecordInput(
                    attempt_id=101,
                    question_id=created.id,
                    selected_option_index=1,
                    is_correct=True,
                    topic_id=4,
                    difficulty_at_attempt="Medium",
                )
            ]
        )

        # Attempt to delete
        was_soft_deleted = repo.delete_question(created.id)
        assert was_soft_deleted is True  # True indicates soft delete

        # Question still exists in DB but is_active is False
        loaded = repo.get_question_by_id(created.id)
        assert loaded is not None
        assert loaded.is_active is False

    def test_get_active_questions_by_topic(self, temp_db):
        """Querying active questions by topic excludes soft-deleted items (FR-12)."""
        session_factory, _ = temp_db
        repo = QuizRepository(session_factory=session_factory)

        q1 = repo.create_question(
            QuestionRecordInput(
                course_id=1,
                topic_id=20,
                statement="Q1 active",
                options=["A", "B"],
                correct_option_index=0,
                difficulty="Easy",
            )
        )
        q2 = repo.create_question(
            QuestionRecordInput(
                course_id=1,
                topic_id=20,
                statement="Q2 active",
                options=["A", "B"],
                correct_option_index=1,
                difficulty="Hard",
            )
        )
        q3 = repo.create_question(
            QuestionRecordInput(
                course_id=1,
                topic_id=20,
                statement="Q3 soft-deleted",
                options=["A", "B"],
                correct_option_index=0,
                difficulty="Medium",
            )
        )

        # Soft delete q3
        repo.record_attempt_answers(
            [
                AnswerRecordInput(
                    attempt_id=201,
                    question_id=q3.id,
                    selected_option_index=0,
                    is_correct=True,
                    topic_id=20,
                    difficulty_at_attempt="Medium",
                )
            ]
        )
        repo.delete_question(q3.id)

        active = repo.get_active_questions_by_topic(course_id=1, topic_id=20)
        assert len(active) == 2
        active_ids = [q.id for q in active]
        assert q1.id in active_ids
        assert q2.id in active_ids
        assert q3.id not in active_ids


class TestQuizRepositoryQuizManagement:
    """Test QuizModel and QuizQuestionModel association, sequencing and publication (FR-10, FR-11)."""

    def test_quiz_creation_and_question_association(self, temp_db):
        """Quiz persists with associated questions in specified sequence order."""
        session_factory, _ = temp_db
        repo = QuizRepository(session_factory=session_factory)

        # Create two questions
        q1 = repo.create_question(
            QuestionRecordInput(
                course_id=2,
                topic_id=1,
                statement="Q1",
                options=["A", "B"],
                correct_option_index=0,
                difficulty="Easy",
            )
        )
        q2 = repo.create_question(
            QuestionRecordInput(
                course_id=2,
                topic_id=1,
                statement="Q2",
                options=["C", "D"],
                correct_option_index=1,
                difficulty="Medium",
            )
        )

        quiz = repo.create_quiz(
            QuizRecordInput(
                course_id=2,
                title="Quiz 1: Fundamentals",
                description="Introductory quiz",
                topic_id=1,
                question_ids=[q2.id, q1.id],  # Specific order: q2 first, then q1
                is_published=False,
            )
        )
        assert quiz.id is not None
        assert quiz.title == "Quiz 1: Fundamentals"
        assert quiz.is_published is False
        assert len(quiz.questions) == 2
        assert quiz.questions[0].id == q2.id
        assert quiz.questions[1].id == q1.id

        # Reload from fresh repository instance
        del repo
        repo_2 = QuizRepository(session_factory=session_factory)
        loaded = repo_2.get_quiz_by_id(quiz.id)
        assert loaded is not None
        assert loaded.title == "Quiz 1: Fundamentals"
        assert len(loaded.questions) == 2
        assert loaded.questions[0].id == q2.id
        assert loaded.questions[1].id == q1.id

    def test_quiz_publish_toggle(self, temp_db):
        """Publishing and unpublishing quizzes works correctly (FR-10)."""
        session_factory, _ = temp_db
        repo = QuizRepository(session_factory=session_factory)

        quiz = repo.create_quiz(
            QuizRecordInput(course_id=1, title="Draft Quiz", question_ids=[], is_published=False)
        )
        assert quiz.is_published is False

        published = repo.set_quiz_published(quiz.id, is_published=True)
        assert published.is_published is True

        reloaded = repo.get_quiz_by_id(quiz.id)
        assert reloaded.is_published is True

        unpublished = repo.set_quiz_published(quiz.id, is_published=False)
        assert unpublished.is_published is False

    def test_get_course_quizzes_published_filter(self, temp_db):
        """Querying quizzes for course supports filtering published-only for students (FR-10)."""
        session_factory, _ = temp_db
        repo = QuizRepository(session_factory=session_factory)

        repo.create_quiz(
            QuizRecordInput(course_id=5, title="Draft Quiz", question_ids=[], is_published=False)
        )
        repo.create_quiz(
            QuizRecordInput(course_id=5, title="Live Quiz", question_ids=[], is_published=True)
        )

        all_quizzes = repo.get_course_quizzes(course_id=5, published_only=False)
        assert len(all_quizzes) == 2

        student_quizzes = repo.get_course_quizzes(course_id=5, published_only=True)
        assert len(student_quizzes) == 1
        assert student_quizzes[0].title == "Live Quiz"


class TestQuizRepositoryAttemptAnswers:
    """Test AttemptAnswerModel recording and retrieval (FR-13, FR-14)."""

    def test_record_and_get_attempt_answers(self, temp_db):
        """Detailed answer records persist and can be queried by attempt ID."""
        session_factory, _ = temp_db
        repo = QuizRepository(session_factory=session_factory)

        q1 = repo.create_question(
            QuestionRecordInput(
                course_id=1,
                topic_id=2,
                statement="Q1",
                options=["A", "B"],
                correct_option_index=0,
                difficulty="Easy",
            )
        )
        q2 = repo.create_question(
            QuestionRecordInput(
                course_id=1,
                topic_id=3,
                statement="Q2",
                options=["X", "Y"],
                correct_option_index=1,
                difficulty="Hard",
            )
        )

        answers_input = [
            AnswerRecordInput(
                attempt_id=500,
                question_id=q1.id,
                selected_option_index=0,
                is_correct=True,
                topic_id=2,
                difficulty_at_attempt="Easy",
            ),
            AnswerRecordInput(
                attempt_id=500,
                question_id=q2.id,
                selected_option_index=0,
                is_correct=False,
                topic_id=3,
                difficulty_at_attempt="Hard",
            ),
        ]
        repo.record_attempt_answers(answers_input)

        loaded_answers = repo.get_attempt_answers(attempt_id=500)
        assert len(loaded_answers) == 2
        assert loaded_answers[0].question_id == q1.id
        assert loaded_answers[0].is_correct is True
        assert loaded_answers[0].difficulty_at_attempt == "Easy"

        assert loaded_answers[1].question_id == q2.id
        assert loaded_answers[1].is_correct is False
        assert loaded_answers[1].difficulty_at_attempt == "Hard"
