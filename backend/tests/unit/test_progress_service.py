"""Unit tests for Student Progress and History Service (AdaptLearn M5).

Requirements Traceability:
- FR-21: Student dashboard showing course completion, topic mastery breakdown,
         recommended topics, and recent attempts.
- FR-15: Student attempt history retrieval with pagination.
- TC-21-1 & TC-21-2: Normal progress view and zero-attempt boundary case.
- NFR-06: Privacy and student-isolated data views.
"""
import pytest

from app.engine.recommendation_strategy import TopicRecommendationInput
from app.repositories.adaptive_repository import AdaptiveRepository
from app.repositories.progress_repository import AttemptRecord, ProgressRepository
from app.services.progress_service import ProgressService


@pytest.fixture
def repos():
    """Create isolated progress and adaptive repositories."""
    prog_repo = ProgressRepository()
    adapt_repo = AdaptiveRepository()
    return prog_repo, adapt_repo


class TestCompletionPercentage:
    """Validate course completion percentage calculation."""

    def test_completion_percentage_partial(self, repos):
        """2 out of 4 topics Proficient yields 50.0% completion."""
        prog_repo, adapt_repo = repos
        course_id = 10
        topics = [
            TopicRecommendationInput(topic_id=1, name="T1", mastery_level="Proficient", score=0.90),
            TopicRecommendationInput(topic_id=2, name="T2", mastery_level="Proficient", score=0.85),
            TopicRecommendationInput(topic_id=3, name="T3", mastery_level="Developing", score=0.60),
            TopicRecommendationInput(topic_id=4, name="T4", mastery_level="Weak", score=0.30),
        ]
        adapt_repo.set_course_topics(course_id, topics)
        prog_repo.enroll_student(student_id=1, course_id=course_id)

        service = ProgressService(progress_repo=prog_repo, adaptive_repo=adapt_repo)
        progress = service.get_student_progress(student_id=1, course_id=course_id)

        assert progress.completion_percentage == 50.0
        assert len(progress.topic_breakdown) == 4

    def test_completion_percentage_empty_course(self, repos):
        """Empty course yields 0.0% completion."""
        prog_repo, adapt_repo = repos
        course_id = 11
        adapt_repo.set_course_topics(course_id, [])
        prog_repo.enroll_student(student_id=1, course_id=course_id)

        service = ProgressService(progress_repo=prog_repo, adaptive_repo=adapt_repo)
        progress = service.get_student_progress(student_id=1, course_id=course_id)

        assert progress.completion_percentage == 0.0
        assert len(progress.topic_breakdown) == 0

    def test_completion_percentage_all_proficient(self, repos):
        """All topics Proficient yields 100.0% completion."""
        prog_repo, adapt_repo = repos
        course_id = 12
        topics = [
            TopicRecommendationInput(topic_id=1, name="T1", mastery_level="Proficient", score=0.88),
            TopicRecommendationInput(topic_id=2, name="T2", mastery_level="Proficient", score=0.95),
        ]
        adapt_repo.set_course_topics(course_id, topics)
        prog_repo.enroll_student(student_id=1, course_id=course_id)

        service = ProgressService(progress_repo=prog_repo, adaptive_repo=adapt_repo)
        progress = service.get_student_progress(student_id=1, course_id=course_id)

        assert progress.completion_percentage == 100.0


class TestTC212StudentWithNoAttempts:
    """Validate TC-21-2 boundary case: student with zero attempts."""

    def test_tc_21_2_zero_attempts_student(self, repos):
        """TC-21-2: A student with no attempts views the dashboard."""
        prog_repo, adapt_repo = repos
        course_id = 20
        topics = [
            TopicRecommendationInput(topic_id=1, name="Basics", mastery_level="Not Assessed", score=0.0),
        ]
        adapt_repo.set_course_topics(course_id, topics)
        prog_repo.enroll_student(student_id=99, course_id=course_id)

        service = ProgressService(progress_repo=prog_repo, adaptive_repo=adapt_repo)
        progress = service.get_student_progress(student_id=99, course_id=course_id)

        assert progress.student_id == 99
        assert progress.course_id == course_id
        assert progress.completion_percentage == 0.0
        assert len(progress.recent_attempts) == 0
        assert len(progress.topic_breakdown) == 1
        assert progress.topic_breakdown[0].mastery_level == "Not Assessed"


class TestAttemptHistoryPagination:
    """Validate paginated attempt history (FR-15)."""

    def test_attempt_history_pagination_pages(self, repos):
        """15 attempts paginated at 5 per page."""
        prog_repo, adapt_repo = repos
        course_id = 30
        student_id = 5
        prog_repo.enroll_student(student_id=student_id, course_id=course_id)

        # Record 15 attempts
        for i in range(1, 16):
            prog_repo.record_attempt(
                AttemptRecord(
                    attempt_id=i,
                    student_id=student_id,
                    course_id=course_id,
                    quiz_id=100 + i,
                    quiz_title=f"Quiz {i}",
                    score=0.50 + (i * 0.02),
                    total_questions=10,
                    submitted_at=f"2026-11-21T0{i:02d}:00:00Z",
                )
            )

        service = ProgressService(progress_repo=prog_repo, adaptive_repo=adapt_repo)

        # Page 1 (limit 5, offset 0)
        p1 = service.get_attempt_history(student_id=student_id, course_id=course_id, page=1, page_size=5)
        assert p1.total_attempts == 15
        assert p1.page == 1
        assert p1.page_size == 5
        assert len(p1.attempts) == 5
        # Most recent first
        assert p1.attempts[0].attempt_id == 15

        # Page 2
        p2 = service.get_attempt_history(student_id=student_id, course_id=course_id, page=2, page_size=5)
        assert len(p2.attempts) == 5
        assert p2.attempts[0].attempt_id == 10

        # Page 4 (out of bounds)
        p4 = service.get_attempt_history(student_id=student_id, course_id=course_id, page=4, page_size=5)
        assert len(p4.attempts) == 0
