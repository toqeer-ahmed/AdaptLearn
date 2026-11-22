"""Unit tests for LearningPathService layer.

Requirements Traceability:
- FR-18: Prerequisite-aware topic unlock evaluation and sequencing.
- FR-19: Recommendation engine tagging with pedagogical rationale.
- FR-20: Cold-start path generation.
- FR-25: Layered architecture and exception boundaries.
- Decision 4: 'Proficient' mastery level is prerequisite unlock threshold.
- Decision 5: Instructor ?student_id parameter.
- NFR-06: Student privacy boundaries.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.engine.mastery_calculator import MasteryParameters
from app.engine.recommendation_strategy import TopicRecommendation
from app.models.course import CourseModel, TopicModel
from app.services.learning_path_service import LearningPathService


@pytest.fixture
def mock_course_repo():
    """Mock CourseRepository."""
    return MagicMock()


@pytest.fixture
def mock_adaptive_repo():
    """Mock AdaptiveRepository."""
    repo = MagicMock()
    repo.get_course_settings.return_value = MasteryParameters(
        window_size=5,
        easy_weight=1.0,
        medium_weight=2.0,
        hard_weight=3.0,
        weak_threshold=0.50,
        proficient_threshold=0.80,
        min_responses=3,
    )
    repo.get_student_topic_responses.return_value = []
    return repo


@pytest.fixture
def mock_strategy_creator():
    """Mock RecommendationStrategyCreator."""
    creator = MagicMock()
    creator.recommend.return_value = []
    return creator


@pytest.fixture
def service(mock_course_repo, mock_adaptive_repo, mock_strategy_creator):
    """LearningPathService wired with mocks."""
    return LearningPathService(
        course_repo=mock_course_repo,
        adaptive_repo=mock_adaptive_repo,
        strategy_creator=mock_strategy_creator,
    )


class TestLearningPathServiceAuthorization:
    """Unit tests for authorization rules in LearningPathService."""

    def test_course_not_found_raises_404(self, service, mock_course_repo):
        """Missing course raises HTTP 404."""
        mock_course_repo.get_course_by_id.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            service.get_learning_path(
                course_id=999,
                student_id=101,
                current_user_id=101,
                current_user_role="student",
            )
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    def test_student_cannot_view_other_student_path_raises_403(self, service, mock_course_repo):
        """Student attempting to view another student's path is rejected with HTTP 403."""
        mock_course_repo.get_course_by_id.return_value = CourseModel(
            id=1, instructor_id=1, title="Test", course_code="CS1"
        )
        with pytest.raises(HTTPException) as exc_info:
            service.get_learning_path(
                course_id=1,
                student_id=102,
                current_user_id=101,
                current_user_role="student",
            )
        assert exc_info.value.status_code == 403
        assert "Students may only view their own" in exc_info.value.detail

    def test_non_enrolled_student_raises_403(self, service, mock_course_repo):
        """Student not enrolled in the course is rejected with HTTP 403."""
        mock_course_repo.get_course_by_id.return_value = CourseModel(
            id=1, instructor_id=1, title="Test", course_code="CS1"
        )
        mock_course_repo.is_student_enrolled.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            service.get_learning_path(
                course_id=1,
                student_id=101,
                current_user_id=101,
                current_user_role="student",
            )
        assert exc_info.value.status_code == 403
        assert "not enrolled" in exc_info.value.detail

    def test_instructor_not_owner_raises_403(self, service, mock_course_repo):
        """Instructor who does not own the course is rejected with HTTP 403."""
        mock_course_repo.get_course_by_id.return_value = CourseModel(
            id=1, instructor_id=2, title="Test", course_code="CS1"
        )
        with pytest.raises(HTTPException) as exc_info:
            service.get_learning_path(
                course_id=1,
                student_id=101,
                current_user_id=1,
                current_user_role="instructor",
            )
        assert exc_info.value.status_code == 403
        assert "not the instructor of this course" in exc_info.value.detail

    def test_unknown_role_raises_403(self, service, mock_course_repo):
        """Unrecognized user role raises HTTP 403."""
        mock_course_repo.get_course_by_id.return_value = CourseModel(
            id=1, instructor_id=1, title="Test", course_code="CS1"
        )
        with pytest.raises(HTTPException) as exc_info:
            service.get_learning_path(
                course_id=1,
                student_id=101,
                current_user_id=101,
                current_user_role="auditor",
            )
        assert exc_info.value.status_code == 403
        assert "Unrecognized user role" in exc_info.value.detail


class TestLearningPathServiceCalculations:
    """Unit tests for path unlocking, recommendations, and metrics."""

    def test_empty_course_returns_zero_metrics(self, service, mock_course_repo):
        """A course with no topics returns empty path and 0% completion."""
        mock_course_repo.get_course_by_id.return_value = CourseModel(
            id=1, instructor_id=1, title="Empty Course", course_code="CS1"
        )
        mock_course_repo.is_student_enrolled.return_value = True
        mock_course_repo.list_course_topics.return_value = []

        resp = service.get_learning_path(
            course_id=1,
            student_id=101,
            current_user_id=101,
            current_user_role="student",
        )
        assert resp.total_topics == 0
        assert resp.unlocked_count == 0
        assert resp.completed_count == 0
        assert resp.completion_percentage == 0.0
        assert resp.path == []

    def test_topics_without_prerequisites_unlocked(
        self, service, mock_course_repo, mock_adaptive_repo
    ):
        """Topics with no prerequisites are always unlocked."""
        mock_course_repo.get_course_by_id.return_value = CourseModel(
            id=1, instructor_id=1, title="Python 101", course_code="PY101"
        )
        mock_course_repo.is_student_enrolled.return_value = True
        t1 = TopicModel(id=10, course_id=1, title="Variables", order_index=0, is_active=True)
        t2 = TopicModel(id=11, course_id=1, title="Conditionals", order_index=1, is_active=True)
        mock_course_repo.list_course_topics.return_value = [t1, t2]
        mock_course_repo.get_prerequisites_for_topic.return_value = []

        resp = service.get_learning_path(
            course_id=1,
            student_id=101,
            current_user_id=101,
            current_user_role="student",
        )
        assert resp.total_topics == 2
        assert resp.unlocked_count == 2
        assert resp.path[0].is_unlocked is True
        assert resp.path[1].is_unlocked is True

    def test_topic_locked_when_prerequisite_not_proficient(
        self, service, mock_course_repo, mock_adaptive_repo
    ):
        """Topic 2 is locked when its prerequisite Topic 1 is Not Assessed or Weak."""
        mock_course_repo.get_course_by_id.return_value = CourseModel(
            id=1, instructor_id=1, title="Course", course_code="C1"
        )
        mock_course_repo.is_student_enrolled.return_value = True
        t1 = TopicModel(id=1, course_id=1, title="Topic 1", order_index=0, is_active=True)
        t2 = TopicModel(id=2, course_id=1, title="Topic 2", order_index=1, is_active=True)
        mock_course_repo.list_course_topics.return_value = [t1, t2]

        def get_prereqs(topic_id: int):
            return [1] if topic_id == 2 else []

        mock_course_repo.get_prerequisites_for_topic.side_effect = get_prereqs

        resp = service.get_learning_path(
            course_id=1,
            student_id=101,
            current_user_id=101,
            current_user_role="student",
        )
        assert resp.path[0].is_unlocked is True
        assert resp.path[1].is_unlocked is False
        assert "not yet Proficient" in resp.path[1].locked_reason

    def test_recommendation_tagging_from_engine(
        self, service, mock_course_repo, mock_adaptive_repo, mock_strategy_creator
    ):
        """Recommendation strategy selections are tagged onto TopicPathItem."""
        mock_course_repo.get_course_by_id.return_value = CourseModel(
            id=1, instructor_id=1, title="Course", course_code="C1"
        )
        mock_course_repo.is_student_enrolled.return_value = True
        t1 = TopicModel(id=1, course_id=1, title="Basics", order_index=0, is_active=True)
        mock_course_repo.list_course_topics.return_value = [t1]
        mock_course_repo.get_prerequisites_for_topic.return_value = []

        mock_strategy_creator.recommend.return_value = [
            TopicRecommendation(
                topic_id=1,
                name="Basics",
                score=0.0,
                mastery_level="Not Assessed",
                rationale="Suggested starting point: foundational topic with no prerequisites.",
            )
        ]

        resp = service.get_learning_path(
            course_id=1,
            student_id=101,
            current_user_id=101,
            current_user_role="student",
        )
        assert resp.path[0].is_recommended is True
        assert "Suggested starting point" in resp.path[0].rationale
