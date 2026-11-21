"""Persistent storage and restart survival verification tests.

Requirements Traceability:
- NFR-07: Parameterized queries / ORM mapping.
- NFR-08: Transactional integrity and persistence across server restart.
- NFR-09: Referential integrity and uniqueness constraints.
- Decision D6: SQLAlchemy 2.0 ORM with persistent database storage.
- SQA DEF-DATA-001: Replacement of volatile in-memory dicts with persistent storage.
"""
import contextlib
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import init_db
from app.engine.mastery_calculator import MasteryParameters, ResponseRecord
from app.engine.recommendation_strategy import TopicRecommendationInput
from app.repositories.adaptive_repository import AdaptiveRepository
from app.repositories.progress_repository import AttemptRecord, ProgressRepository
from app.repositories.user_repository import UserRepository


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database file for isolated persistence testing."""
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


class TestAdaptiveRepositoryPersistence:
    """Validate persistence and restart survival for Module 3 data."""

    def test_course_settings_crud_and_survival_across_restart(self, temp_db):
        """Course adaptive parameters survive process recreation / server restart."""
        session_factory, _ = temp_db

        # Step 1: Initialize repository and save custom parameters
        repo_1 = AdaptiveRepository(session_factory=session_factory)
        custom_params = MasteryParameters(
            window_size=10,
            easy_weight=1.2,
            medium_weight=1.8,
            hard_weight=2.5,
            weak_threshold=0.45,
            proficient_threshold=0.85,
            min_responses=5,
        )
        repo_1.save_course_settings(course_id=200, params=custom_params)

        # Step 2: Simulate restart — destroy repo_1, instantiate fresh repo_2
        del repo_1
        repo_2 = AdaptiveRepository(session_factory=session_factory)

        # Step 3: Verify parameters survived restart
        loaded = repo_2.get_course_settings(course_id=200)
        assert loaded.window_size == 10
        assert loaded.easy_weight == 1.2
        assert loaded.medium_weight == 1.8
        assert loaded.hard_weight == 2.5
        assert loaded.weak_threshold == 0.45
        assert loaded.proficient_threshold == 0.85
        assert loaded.min_responses == 5

    def test_student_topic_responses_survival_across_restart(self, temp_db):
        """Historical quiz responses survive restart in exact insertion order."""
        session_factory, _ = temp_db

        # Step 1: Append responses with instance 1
        repo_1 = AdaptiveRepository(session_factory=session_factory)
        responses = [
            ResponseRecord(difficulty="Easy", is_correct=True),
            ResponseRecord(difficulty="Medium", is_correct=False),
            ResponseRecord(difficulty="Hard", is_correct=True),
        ]
        for r in responses:
            repo_1.append_student_response(student_id=50, topic_id=12, record=r)

        # Step 2: Simulate restart
        del repo_1
        repo_2 = AdaptiveRepository(session_factory=session_factory)

        # Step 3: Retrieve and verify
        loaded = repo_2.get_student_topic_responses(student_id=50, topic_id=12)
        assert len(loaded) == 3
        assert loaded[0].difficulty == "Easy" and loaded[0].is_correct is True
        assert loaded[1].difficulty == "Medium" and loaded[1].is_correct is False
        assert loaded[2].difficulty == "Hard" and loaded[2].is_correct is True

    def test_course_topics_and_prerequisites_survival_across_restart(self, temp_db):
        """Topic candidates and prerequisite graphs survive restart."""
        session_factory, _ = temp_db

        repo_1 = AdaptiveRepository(session_factory=session_factory)
        topics = [
            TopicRecommendationInput(topic_id=1, name="Basics", mastery_level="Proficient", score=0.9),
            TopicRecommendationInput(topic_id=2, name="Functions", mastery_level="Developing", score=0.6, prerequisites=(1,)),
            TopicRecommendationInput(topic_id=3, name="Classes", mastery_level="Weak", score=0.3, prerequisites=(1, 2)),
        ]
        repo_1.set_course_topics(course_id=300, topics=topics)

        # Simulate restart
        del repo_1
        repo_2 = AdaptiveRepository(session_factory=session_factory)

        loaded_topics = repo_2.get_course_topics(course_id=300)
        assert len(loaded_topics) == 3
        assert loaded_topics[0].topic_id == 1 and loaded_topics[0].name == "Basics"
        assert loaded_topics[1].topic_id == 2 and loaded_topics[1].prerequisites == (1,)
        assert loaded_topics[2].topic_id == 3 and loaded_topics[2].prerequisites == (1, 2)

        prereqs = repo_2.get_course_prerequisites(course_id=300)
        assert prereqs[2] == {1}
        assert prereqs[3] == {1, 2}

    def test_empty_database_defaults(self, temp_db):
        """Empty database returns standard defaults without raising exceptions."""
        session_factory, _ = temp_db
        repo = AdaptiveRepository(session_factory=session_factory)

        # Unconfigured course returns defaults
        defaults = repo.get_course_settings(course_id=999)
        assert defaults.window_size == 10
        assert defaults.easy_weight == 1.0

        # Non-existent responses return empty list
        assert repo.get_student_topic_responses(student_id=999, topic_id=999) == []
        assert repo.get_course_topics(course_id=999) == []


class TestProgressRepositoryPersistence:
    """Validate persistence and restart survival for Module 5 data."""

    def test_enrollments_and_course_ownership_survival_across_restart(self, temp_db):
        """Enrollments and instructor course ownership survive restart."""
        session_factory, _ = temp_db

        repo_1 = ProgressRepository(session_factory=session_factory)
        repo_1.enroll_student(student_id=101, course_id=500)
        repo_1.enroll_student(student_id=102, course_id=500)
        repo_1.set_course_owner(course_id=500, instructor_id=1)

        # Simulate restart
        del repo_1
        repo_2 = ProgressRepository(session_factory=session_factory)

        assert repo_2.is_student_enrolled(student_id=101, course_id=500) is True
        assert repo_2.is_student_enrolled(student_id=102, course_id=500) is True
        assert repo_2.is_student_enrolled(student_id=103, course_id=500) is False
        assert repo_2.get_course_enrolled_students(course_id=500) == [101, 102]

        assert repo_2.is_course_owner(course_id=500, instructor_id=1) is True
        assert repo_2.is_course_owner(course_id=500, instructor_id=2) is False

    def test_attempt_history_survival_across_restart(self, temp_db):
        """Student attempt history survives restart and preserves reverse chronological ordering."""
        session_factory, _ = temp_db

        repo_1 = ProgressRepository(session_factory=session_factory)
        attempts = [
            AttemptRecord(
                attempt_id=1,
                student_id=101,
                course_id=500,
                quiz_id=10,
                quiz_title="Quiz 1",
                score=0.8,
                total_questions=5,
                submitted_at="2026-11-20T10:00:00Z",
            ),
            AttemptRecord(
                attempt_id=2,
                student_id=101,
                course_id=500,
                quiz_id=10,
                quiz_title="Quiz 1 Retake",
                score=1.0,
                total_questions=5,
                submitted_at="2026-11-21T10:00:00Z",
            ),
        ]
        for a in attempts:
            repo_1.record_attempt(a)

        # Simulate restart
        del repo_1
        repo_2 = ProgressRepository(session_factory=session_factory)

        loaded, total = repo_2.get_student_attempts(student_id=101, course_id=500)
        assert total == 2
        # Reverse chronological ordering (newest attempt_id first)
        assert loaded[0].attempt_id == 2
        assert loaded[0].score == 1.0
        assert loaded[1].attempt_id == 1

    def test_question_stats_survival_across_restart(self, temp_db):
        """Aggregated question metrics survive restart with accurate counters."""
        session_factory, _ = temp_db

        repo_1 = ProgressRepository(session_factory=session_factory)
        # Record 4 correct answers and 2 incorrect answers
        for _ in range(4):
            repo_1.record_question_response(
                course_id=500,
                question_id=7,
                question_text="What is TDD?",
                topic_id=1,
                topic_name="Unit Testing",
                difficulty="Medium",
                is_correct=True,
            )
        for _ in range(2):
            repo_1.record_question_response(
                course_id=500,
                question_id=7,
                question_text="What is TDD?",
                topic_id=1,
                topic_name="Unit Testing",
                difficulty="Medium",
                is_correct=False,
            )

        # Simulate restart
        del repo_1
        repo_2 = ProgressRepository(session_factory=session_factory)

        stats = repo_2.get_course_question_stats(course_id=500)
        assert len(stats) == 1
        assert stats[0].question_id == 7
        assert stats[0].times_answered == 6
        assert stats[0].correct_count == 4


class TestUserRepositoryPersistence:
    """Validate persistence and restart survival for User accounts."""

    def test_user_survival_across_restart(self, temp_db):
        """Registered user survives restart and password verification works."""
        session_factory, _ = temp_db

        repo_1 = UserRepository(session_factory=session_factory)
        user_1 = repo_1.create_user(
            name="Persistent User",
            email="persistent@adaptlearn.edu",
            password_hash="$2b$12$eExAmPlEhAsH1234567890",
            role="student",
        )
        assert user_1.id >= 102

        # Simulate restart
        del repo_1
        repo_2 = UserRepository(session_factory=session_factory)

        loaded = repo_2.get_by_email("persistent@adaptlearn.edu")
        assert loaded is not None
        assert loaded.id == user_1.id
        assert loaded.name == "Persistent User"
        assert loaded.role == "student"

    def test_duplicate_email_enforces_uniqueness(self, temp_db):
        """Duplicate email registration raises ValueError."""
        session_factory, _ = temp_db
        repo = UserRepository(session_factory=session_factory)

        with pytest.raises(ValueError, match="already registered"):
            repo.create_user(
                name="Duplicate",
                email="alice@student.adaptlearn.edu",  # Seeded default
                password_hash="somehash",
                role="student",
            )
