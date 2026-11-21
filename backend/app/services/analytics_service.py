"""Business logic service for instructor analytics and reporting (AdaptLearn M5).

Architecture & Layering:
Service -> ProgressRepository & AdaptiveRepository
Service -> Engine (MasteryCalculator for evaluating student mastery levels)

Per M1 Section 9.1:
Module 5 reads data across modules 1 to 4 to build read-only analytical aggregations.
It avoids duplicating grading or mastery classification logic.
"""

from app.engine.mastery_calculator import MasteryCalculator
from app.repositories.adaptive_repository import (
    AdaptiveRepository,
    get_adaptive_repository,
)
from app.repositories.progress_repository import (
    ProgressRepository,
    get_progress_repository,
)
from app.schemas.analytics import (
    CourseQuestionStatsResponse,
    MasteryDistributionResponse,
    QuestionStatItem,
    StudentRosterMasteryItem,
    StudentRosterResponse,
    StudentTopicMasteryItem,
    TopicMasteryDistributionItem,
)


class AnalyticsService:
    """Service producing aggregated course progress and question performance analytics."""

    def __init__(
        self,
        progress_repo: ProgressRepository | None = None,
        adaptive_repo: AdaptiveRepository | None = None,
    ) -> None:
        self.progress_repo = progress_repo or get_progress_repository()
        self.adaptive_repo = adaptive_repo or get_adaptive_repository()

    def get_mastery_distribution(self, course_id: int) -> MasteryDistributionResponse:
        """Aggregate student counts per mastery level across all course topics (FR-23)."""
        student_ids = self.progress_repo.get_course_enrolled_students(course_id)
        topics = self.adaptive_repo.get_course_topics(course_id)
        course_params = self.adaptive_repo.get_course_settings(course_id)
        calculator = MasteryCalculator.from_parameters(course_params)

        topic_distributions: list[TopicMasteryDistributionItem] = []

        for topic in topics:
            weak = developing = proficient = not_assessed = 0

            for s_id in student_ids:
                responses = self.adaptive_repo.get_student_topic_responses(
                    student_id=s_id, topic_id=topic.topic_id
                )
                if responses:
                    res = calculator.calculate_mastery(responses)
                    level = res.level
                else:
                    level = "Not Assessed"

                if level == "Weak":
                    weak += 1
                elif level == "Developing":
                    developing += 1
                elif level == "Proficient":
                    proficient += 1
                else:
                    not_assessed += 1

            topic_distributions.append(
                TopicMasteryDistributionItem(
                    topic_id=topic.topic_id,
                    topic_name=topic.name,
                    weak_count=weak,
                    developing_count=developing,
                    proficient_count=proficient,
                    not_assessed_count=not_assessed,
                    total_students=len(student_ids),
                )
            )

        return MasteryDistributionResponse(
            course_id=course_id,
            total_enrolled=len(student_ids),
            topics=topic_distributions,
        )

    def get_student_roster(self, course_id: int) -> StudentRosterResponse:
        """Produce the enrolled student roster matrix with per-topic mastery scores (FR-22)."""
        student_ids = self.progress_repo.get_course_enrolled_students(course_id)
        topics = self.adaptive_repo.get_course_topics(course_id)
        course_params = self.adaptive_repo.get_course_settings(course_id)
        calculator = MasteryCalculator.from_parameters(course_params)

        roster: list[StudentRosterMasteryItem] = []

        for s_id in student_ids:
            student_masteries: list[StudentTopicMasteryItem] = []
            for topic in topics:
                responses = self.adaptive_repo.get_student_topic_responses(
                    student_id=s_id, topic_id=topic.topic_id
                )
                if responses:
                    res = calculator.calculate_mastery(responses)
                    score = res.score
                    level = res.level
                else:
                    score = 0.0
                    level = "Not Assessed"

                student_masteries.append(
                    StudentTopicMasteryItem(
                        topic_id=topic.topic_id,
                        topic_name=topic.name,
                        score=score,
                        mastery_level=level,
                    )
                )

            roster.append(
                StudentRosterMasteryItem(
                    student_id=s_id,
                    student_name=f"Student {s_id}",
                    topic_masteries=student_masteries,
                )
            )

        return StudentRosterResponse(
            course_id=course_id,
            total_students=len(roster),
            students=roster,
        )

    def get_question_stats(self, course_id: int) -> CourseQuestionStatsResponse:
        """Compute question-level answering statistics and difficulty percentage (FR-24)."""
        stats_records = self.progress_repo.get_course_question_stats(course_id)

        items: list[QuestionStatItem] = []
        for stat in stats_records:
            pct = (
                round((stat.correct_count / stat.times_answered) * 100.0, 1)
                if stat.times_answered > 0
                else 0.0
            )
            items.append(
                QuestionStatItem(
                    question_id=stat.question_id,
                    question_text=stat.question_text,
                    topic_id=stat.topic_id,
                    topic_name=stat.topic_name,
                    difficulty=stat.difficulty,
                    times_answered=stat.times_answered,
                    correct_count=stat.correct_count,
                    correct_percentage=pct,
                )
            )

        return CourseQuestionStatsResponse(
            course_id=course_id,
            total_questions=len(items),
            questions=items,
        )


def get_analytics_service() -> AnalyticsService:
    """FastAPI dependency provider for AnalyticsService."""
    return AnalyticsService()
