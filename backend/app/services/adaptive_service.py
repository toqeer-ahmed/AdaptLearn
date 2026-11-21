"""Application service for adaptive learning coordination (AdaptLearn M3).

Architecture & Layering:
Service -> Repository (for persistence)
Service -> Engine (pure domain calculations)

This module coordinates business rules, orchestrates the engine, and maps
domain results to API schema contracts. It contains ZERO web router or SQL logic.
"""

from app.engine.mastery_calculator import (
    MasteryCalculator,
    MasteryParameters,
    ResponseRecord,
)
from app.engine.mastery_policy import InvalidPolicyConfiguration, MasteryPolicy
from app.engine.recommendation_strategy import (
    RecommendationStrategyCreator,
    TopicRecommendationInput,
    get_recommendation_strategy,
    get_strategy_creator,
)
from app.repositories.adaptive_repository import (
    AdaptiveRepository,
    get_adaptive_repository,
)
from app.schemas.adaptive import (
    AdaptiveSettingsResponse,
    AdaptiveSettingsUpdate,
    AttemptMasteryRecalculateRequest,
    AttemptMasteryRecalculateResponse,
    RecommendationListResponse,
    TopicMasteryItem,
    TopicRecommendationResponse,
)


class AdaptiveService:
    """Service orchestrating adaptive parameter management, mastery updates, and recommendations."""

    def __init__(
        self,
        repository: AdaptiveRepository | None = None,
        strategy_creator: RecommendationStrategyCreator | None = None,
    ) -> None:
        self.repository = repository or get_adaptive_repository()
        self.strategy_creator = strategy_creator

    def get_course_settings(self, course_id: int) -> AdaptiveSettingsResponse:
        """Retrieve current adaptive parameters for a course (FR-20)."""
        params = self.repository.get_course_settings(course_id)
        return AdaptiveSettingsResponse(
            course_id=course_id,
            window_size=params.window_size,
            easy_weight=params.easy_weight,
            medium_weight=params.medium_weight,
            hard_weight=params.hard_weight,
            weak_threshold=params.weak_threshold,
            proficient_threshold=params.proficient_threshold,
            min_responses=params.min_responses,
        )

    def update_course_settings(
        self, course_id: int, update: AdaptiveSettingsUpdate
    ) -> AdaptiveSettingsResponse:
        """Update configurable adaptive parameters for a course (FR-20)."""
        current = self.repository.get_course_settings(course_id)

        # Merge updates with current parameters
        new_window = update.window_size if update.window_size is not None else current.window_size
        new_easy = update.easy_weight if update.easy_weight is not None else current.easy_weight
        new_med = update.medium_weight if update.medium_weight is not None else current.medium_weight
        new_hard = update.hard_weight if update.hard_weight is not None else current.hard_weight
        new_weak = update.weak_threshold if update.weak_threshold is not None else current.weak_threshold
        new_prof = (
            update.proficient_threshold
            if update.proficient_threshold is not None
            else current.proficient_threshold
        )
        new_min_resp = (
            update.min_responses if update.min_responses is not None else current.min_responses
        )

        # Validate domain threshold constraints
        if new_weak >= new_prof:
            raise InvalidPolicyConfiguration(
                f"weak_threshold ({new_weak}) must be strictly less than "
                f"proficient_threshold ({new_prof})"
            )

        # Validate by instantiating policy (ensures parameters are mathematically sound)
        MasteryPolicy(
            weak_threshold=new_weak,
            proficient_threshold=new_prof,
            min_responses=new_min_resp,
        )

        new_params = MasteryParameters(
            window_size=new_window,
            easy_weight=new_easy,
            medium_weight=new_med,
            hard_weight=new_hard,
            weak_threshold=new_weak,
            proficient_threshold=new_prof,
            min_responses=new_min_resp,
        )

        saved = self.repository.save_course_settings(course_id, new_params)
        return AdaptiveSettingsResponse(
            course_id=course_id,
            window_size=saved.window_size,
            easy_weight=saved.easy_weight,
            medium_weight=saved.medium_weight,
            hard_weight=saved.hard_weight,
            weak_threshold=saved.weak_threshold,
            proficient_threshold=saved.proficient_threshold,
            min_responses=saved.min_responses,
        )

    def get_recommendations(
        self,
        course_id: int,
        student_id: int = 1,
        limit: int | None = None,
        strategy_name: str = "rule_based",
    ) -> RecommendationListResponse:
        """Generate ordered topic recommendations for a student in a course (FR-18, FR-19)."""
        topics: list[TopicRecommendationInput] = self.repository.get_course_topics(course_id)
        prereqs = self.repository.get_course_prerequisites(course_id)

        creator = self.strategy_creator or get_strategy_creator(strategy_name)
        recommendations = creator.recommend(
            topics=topics,
            prerequisites=prereqs,
            max_recommendations=limit,
        )

        rec_responses = [
            TopicRecommendationResponse(
                topic_id=r.topic_id,
                topic_name=r.name,
                mastery_level=r.mastery_level,
                score=r.score,
                rationale=r.rationale,
            )
            for r in recommendations
        ]

        return RecommendationListResponse(
            course_id=course_id,
            recommendations=rec_responses,
            total_recommended=len(rec_responses),
        )

    def recalculate_attempt_mastery(
        self, request: AttemptMasteryRecalculateRequest
    ) -> AttemptMasteryRecalculateResponse:
        """Recalculate mastery across all affected topics following a quiz submission (FR-16)."""
        course_params = self.repository.get_course_settings(request.course_id)
        calculator = MasteryCalculator.from_parameters(course_params)

        # Append new responses to repository history
        for item in request.responses:
            record = ResponseRecord(
                is_correct=item.is_correct,
                difficulty=item.difficulty,
                topic_id=item.topic_id,
            )
            self.repository.append_student_response(
                student_id=request.student_id,
                topic_id=item.topic_id,
                record=record,
            )

        # Unique topic IDs in the attempt
        affected_topic_ids = sorted({item.topic_id for item in request.responses})
        updated_topics: list[TopicMasteryItem] = []

        for topic_id in affected_topic_ids:
            all_responses = self.repository.get_student_topic_responses(
                student_id=request.student_id,
                topic_id=topic_id,
            )
            result = calculator.calculate_mastery(all_responses)
            updated_topics.append(
                TopicMasteryItem(
                    topic_id=topic_id,
                    score=result.score,
                    level=result.level,
                    response_count=result.response_count,
                )
            )

        return AttemptMasteryRecalculateResponse(
            student_id=request.student_id,
            course_id=request.course_id,
            updated_topics=updated_topics,
        )


def get_adaptive_service() -> AdaptiveService:
    """FastAPI dependency provider for AdaptiveService."""
    return AdaptiveService()

