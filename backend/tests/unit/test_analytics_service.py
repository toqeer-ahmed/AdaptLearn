"""Unit tests for Instructor Analytics Service (AdaptLearn M5).

Requirements Traceability:
- FR-22: View enrolled students with their mastery level in each topic (student roster).
- FR-23: View the number of students at each mastery level per topic (mastery distribution).
- FR-24: View question statistics (times answered and percentage correct).
- TC-24-2: Boundary case — topic/question with zero answers.
"""
import pytest

from app.engine.mastery_calculator import ResponseRecord
from app.engine.recommendation_strategy import TopicRecommendationInput
from app.repositories.adaptive_repository import AdaptiveRepository
from app.repositories.progress_repository import ProgressRepository
from app.services.analytics_service import AnalyticsService


@pytest.fixture
def repos():
    """Fixture providing isolated progress and adaptive repositories."""
    p_repo = ProgressRepository()
    a_repo = AdaptiveRepository()
    return p_repo, a_repo


class TestMasteryDistributionAggregation:
    """Validate FR-23: topic mastery distribution aggregations."""

    def test_mastery_distribution_counts(self, repos):
        """FR-23: 4 students with distinct mastery levels in a topic."""
        p_repo, a_repo = repos
        course_id = 501
        topic_id = 1

        a_repo.set_course_topics(
            course_id,
            [TopicRecommendationInput(topic_id=topic_id, name="Recursion", mastery_level="Not Assessed", score=0.0)],
        )

        # 4 students enrolled
        for s_id in range(1, 5):
            p_repo.enroll_student(s_id, course_id)

        # Student 1: Weak (3 incorrect Easy) -> score 0.0, Weak
        for _ in range(3):
            a_repo.append_student_response(1, topic_id, ResponseRecord(is_correct=False, difficulty="Easy"))

        # Student 2: Developing (1 Easy correct, 1 Hard incorrect, 1 Medium correct) -> score 3/6 = 0.50, Developing
        a_repo.append_student_response(2, topic_id, ResponseRecord(is_correct=True, difficulty="Easy"))
        a_repo.append_student_response(2, topic_id, ResponseRecord(is_correct=False, difficulty="Hard"))
        a_repo.append_student_response(2, topic_id, ResponseRecord(is_correct=True, difficulty="Medium"))

        # Student 3: Proficient (3 Easy correct) -> score 1.0, Proficient
        for _ in range(3):
            a_repo.append_student_response(3, topic_id, ResponseRecord(is_correct=True, difficulty="Easy"))

        # Student 4: Not Assessed (0 responses)

        service = AnalyticsService(progress_repo=p_repo, adaptive_repo=a_repo)
        dist = service.get_mastery_distribution(course_id)

        assert dist.course_id == course_id
        assert dist.total_enrolled == 4
        assert len(dist.topics) == 1

        t_dist = dist.topics[0]
        assert t_dist.topic_id == topic_id
        assert t_dist.topic_name == "Recursion"
        assert t_dist.weak_count == 1
        assert t_dist.developing_count == 1
        assert t_dist.proficient_count == 1
        assert t_dist.not_assessed_count == 1
        assert t_dist.total_students == 4


class TestStudentRosterMatrix:
    """Validate FR-22: enrolled student roster with per-topic mastery."""

    def test_student_roster_matrix(self, repos):
        """FR-22: Roster lists all enrolled students and their topic mastery."""
        p_repo, a_repo = repos
        course_id = 502
        topics = [
            TopicRecommendationInput(topic_id=1, name="T1", mastery_level="Not Assessed", score=0.0),
            TopicRecommendationInput(topic_id=2, name="T2", mastery_level="Not Assessed", score=0.0),
        ]
        a_repo.set_course_topics(course_id, topics)

        p_repo.enroll_student(10, course_id)
        p_repo.enroll_student(20, course_id)

        service = AnalyticsService(progress_repo=p_repo, adaptive_repo=a_repo)
        roster = service.get_student_roster(course_id)

        assert roster.course_id == course_id
        assert roster.total_students == 2
        assert len(roster.students) == 2
        assert {s.student_id for s in roster.students} == {10, 20}
        assert len(roster.students[0].topic_masteries) == 2


class TestQuestionStatistics:
    """Validate FR-24 and TC-24-2: question statistics and boundary conditions."""

    def test_question_statistics_calculation(self, repos):
        """FR-24: Question answered 10 times with 7 correct yields 70.0%."""
        p_repo, a_repo = repos
        course_id = 503

        p_repo.record_question_response(
            course_id=course_id,
            question_id=101,
            question_text="What is a pointer?",
            topic_id=1,
            topic_name="Memory",
            difficulty="Medium",
            is_correct=True,
            count=7,
        )
        p_repo.record_question_response(
            course_id=course_id,
            question_id=101,
            question_text="What is a pointer?",
            topic_id=1,
            topic_name="Memory",
            difficulty="Medium",
            is_correct=False,
            count=3,
        )

        service = AnalyticsService(progress_repo=p_repo, adaptive_repo=a_repo)
        stats = service.get_question_stats(course_id)

        assert stats.course_id == course_id
        assert len(stats.questions) == 1
        q = stats.questions[0]
        assert q.question_id == 101
        assert q.times_answered == 10
        assert q.correct_count == 7
        assert q.correct_percentage == 70.0

    def test_question_statistics_boundary_zero_answers_tc_24_2(self, repos):
        """TC-24-2: Question never answered yields 0 times answered and 0.0%."""
        p_repo, a_repo = repos
        course_id = 504

        p_repo.add_course_question(
            course_id=course_id,
            question_id=202,
            question_text="Explain polymorphism",
            topic_id=2,
            topic_name="OOP",
            difficulty="Hard",
        )

        service = AnalyticsService(progress_repo=p_repo, adaptive_repo=a_repo)
        stats = service.get_question_stats(course_id)

        assert len(stats.questions) == 1
        q = stats.questions[0]
        assert q.times_answered == 0
        assert q.correct_count == 0
        assert q.correct_percentage == 0.0
