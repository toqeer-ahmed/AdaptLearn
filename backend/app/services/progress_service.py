"""Business logic service for student progress, dashboard, and attempt history (AdaptLearn M5).

Architecture & Layering:
Service -> ProgressRepository & AdaptiveRepository
Service -> Engine (for recommendations and score calculations)

Per M1 Section 9.1:
Module 5 reads data from Modules 1 to 4; it contains read-only dashboard assembly logic,
reusing mastery calculation and recommendation logic without duplication.
"""

from app.engine.mastery_calculator import MasteryCalculator
from app.engine.recommendation_strategy import (
    RuleBasedRecommendationStrategy,
    TopicRecommendationInput,
)
from app.repositories.adaptive_repository import (
    AdaptiveRepository,
    get_adaptive_repository,
)
from app.repositories.progress_repository import (
    ProgressRepository,
    get_progress_repository,
)
from app.schemas.adaptive import TopicRecommendationResponse
from app.schemas.progress import (
    AttemptHistoryResponse,
    AttemptSummaryItem,
    StudentProgressResponse,
    TopicProgressItem,
)


class ProgressService:
    """Service consolidating student progress, topic mastery, and attempt histories."""

    def __init__(
        self,
        progress_repo: ProgressRepository | None = None,
        adaptive_repo: AdaptiveRepository | None = None,
    ) -> None:
        self.progress_repo = progress_repo or get_progress_repository()
        self.adaptive_repo = adaptive_repo or get_adaptive_repository()

    def get_student_progress(self, student_id: int, course_id: int) -> StudentProgressResponse:
        """Consolidate student course progress dashboard (FR-21).

        1. Computes mastery score and level for each course topic.
        2. Calculates overall course completion percentage (% of topics Proficient).
        3. Obtains pedagogical topic recommendations via Module 3/4 RecommendationStrategy.
        4. Fetches recent quiz attempts.
        """
        raw_topics = self.adaptive_repo.get_course_topics(course_id)
        course_params = self.adaptive_repo.get_course_settings(course_id)
        calculator = MasteryCalculator.from_parameters(course_params)

        topic_breakdown: list[TopicProgressItem] = []
        topic_inputs_for_rec: list[TopicRecommendationInput] = []
        proficient_count = 0

        for t in raw_topics:
            # Check student's historical responses for this topic
            responses = self.adaptive_repo.get_student_topic_responses(
                student_id=student_id, topic_id=t.topic_id
            )

            if responses:
                result = calculator.calculate_mastery(responses)
                score = result.score
                level = result.level
            else:
                score = t.score if t.mastery_level != "Not Assessed" else 0.0
                level = t.mastery_level

            if level == "Proficient":
                proficient_count += 1

            topic_breakdown.append(
                TopicProgressItem(
                    topic_id=t.topic_id,
                    topic_name=t.name,
                    score=score,
                    mastery_level=level,
                )
            )

            topic_inputs_for_rec.append(
                TopicRecommendationInput(
                    topic_id=t.topic_id,
                    name=t.name,
                    mastery_level=level,
                    score=score,
                    prerequisites=t.prerequisites,
                )
            )

        # Completion percentage
        total_topics = len(raw_topics)
        completion_pct = (
            round((proficient_count / total_topics) * 100.0, 1)
            if total_topics > 0
            else 0.0
        )

        # Recommendations via M3/M4 RuleBasedRecommendationStrategy
        prereqs = self.adaptive_repo.get_course_prerequisites(course_id)
        strategy = RuleBasedRecommendationStrategy()
        raw_recs = strategy.recommend(
            topics=topic_inputs_for_rec,
            prerequisites=prereqs,
            max_recommendations=3,
        )

        recommended_topics = [
            TopicRecommendationResponse(
                topic_id=r.topic_id,
                topic_name=r.name,
                mastery_level=r.mastery_level,
                score=r.score,
                rationale=r.rationale,
            )
            for r in raw_recs
        ]

        # Recent attempts (up to 5)
        recent_records, _ = self.progress_repo.get_student_attempts(
            student_id=student_id, course_id=course_id, limit=5, offset=0
        )
        recent_attempts = [
            AttemptSummaryItem(
                attempt_id=a.attempt_id,
                quiz_id=a.quiz_id,
                quiz_title=a.quiz_title,
                score=a.score,
                total_questions=a.total_questions,
                submitted_at=a.submitted_at,
            )
            for a in recent_records
        ]

        return StudentProgressResponse(
            course_id=course_id,
            student_id=student_id,
            completion_percentage=completion_pct,
            topic_breakdown=topic_breakdown,
            recommended_topics=recommended_topics,
            recent_attempts=recent_attempts,
        )

    def get_attempt_history(
        self, student_id: int, course_id: int, page: int = 1, page_size: int = 10
    ) -> AttemptHistoryResponse:
        """Retrieve paginated attempt history for an enrolled student (FR-15)."""
        offset = max(0, (page - 1) * page_size)
        records, total_count = self.progress_repo.get_student_attempts(
            student_id=student_id,
            course_id=course_id,
            limit=page_size,
            offset=offset,
        )

        items = [
            AttemptSummaryItem(
                attempt_id=a.attempt_id,
                quiz_id=a.quiz_id,
                quiz_title=a.quiz_title,
                score=a.score,
                total_questions=a.total_questions,
                submitted_at=a.submitted_at,
            )
            for a in records
        ]

        return AttemptHistoryResponse(
            course_id=course_id,
            student_id=student_id,
            total_attempts=total_count,
            page=page,
            page_size=page_size,
            attempts=items,
        )


def get_progress_service() -> ProgressService:
    """FastAPI dependency provider for ProgressService."""
    return ProgressService()
