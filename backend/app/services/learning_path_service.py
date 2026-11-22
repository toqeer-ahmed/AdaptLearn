"""Service layer for Module 4: Personalized Learning Paths (AdaptLearn M4).

Requirements Traceability:
- FR-18: Prerequisite-aware unlocking of topics in an ordered learning path.
- FR-19: Pedagogical recommendation tagging via M3 recommendation engine.
- FR-20: Cold-start starting points for students with no attempts.
- FR-25: Defensive validation and architectural contracts.
- Decision 4: 'Proficient' mastery level (>= 0.80) is the prerequisite-unlock threshold.
- Decision 5: Instructor can view ?student_id= for a specific student's path.
- NFR-06: Privacy -- a student can only view their own learning path.

Architecture: M4 is stateless. No new DB tables are created.
Data is sourced from:
  - CourseRepository (M1): topics, prerequisites, enrollment checks.
  - AdaptiveRepository (M3): response history, course settings.
  - MasteryCalculator (M3 engine): mastery scoring and classification.
  - RecommendationStrategyCreator (M3 engine): pedagogical recommendations.
"""

from fastapi import HTTPException, status

from app.engine.mastery_calculator import MasteryCalculator
from app.engine.recommendation_strategy import (
    RecommendationStrategyCreator,
    TopicRecommendationInput,
    get_strategy_creator,
)
from app.repositories.adaptive_repository import (
    AdaptiveRepository,
    get_adaptive_repository,
)
from app.repositories.course_repository import (
    CourseRepository,
    get_course_repository,
)
from app.schemas.learning_path import LearningPathResponse, TopicPathItem

# Proficient level string -- must match MasteryCalculator output exactly
_PROFICIENT = "Proficient"


class LearningPathService:
    """Stateless service that computes a personalized, prerequisite-aware learning path.

    Two-phase algorithm:
      Phase 1 -- Syllabus traversal & prerequisite unlocking:
        For each topic (ordered by order_index ASC), a topic is unlocked only
        when ALL its prerequisite topics have mastery level == 'Proficient'.
      Phase 2 -- Pedagogical recommendation tagging (via M3 engine):
        Unlocked, non-Proficient topics are passed to RuleBasedRecommendationStrategy.
        The strategy assigns is_recommended=True and a rationale to selected topics.

    Authorization rules:
      - Student: must be enrolled in the course; can only view their own path.
      - Instructor: must own the course (instructor_id == current_user_id).
      - Instructor with ?student_id: allowed by Decision 5.
    """

    def __init__(
        self,
        course_repo: CourseRepository | None = None,
        adaptive_repo: AdaptiveRepository | None = None,
        strategy_creator: RecommendationStrategyCreator | None = None,
    ) -> None:
        self.course_repo = course_repo or get_course_repository()
        self.adaptive_repo = adaptive_repo or get_adaptive_repository()
        self.strategy_creator = strategy_creator or get_strategy_creator("rule_based")

    # =========================================================================
    # Main Public Method
    # =========================================================================

    def get_learning_path(
        self,
        course_id: int,
        student_id: int,
        current_user_id: int,
        current_user_role: str,
    ) -> LearningPathResponse:
        """Compute the personalized learning path for a student in a course.

        Args:
            course_id: ID of the course to generate the path for.
            student_id: The student whose mastery data is used.
            current_user_id: User ID of the authenticated requester.
            current_user_role: Role of the authenticated requester ('student' or 'instructor').

        Returns:
            LearningPathResponse with ordered TopicPathItem objects.

        Raises:
            HTTPException(404): Course not found.
            HTTPException(403): Authorization failure.
        """
        role = current_user_role.lower().strip()

        # --- Step 1: Resolve the course (404 if missing) ----------------------
        course = self.course_repo.get_course_by_id(course_id)
        if course is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course {course_id} not found",
            )

        # --- Step 2: Authorization --------------------------------------------
        if role == "student":
            # Students can only view their own path (NFR-06)
            if student_id != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: Students may only view their own learning path",
                )
            if not self.course_repo.is_student_enrolled(student_id, course_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You are not enrolled in this course",
                )
        elif role == "instructor":
            # Instructors must own the course
            if course.instructor_id != current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You are not the instructor of this course",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Unrecognized user role",
            )

        # --- Step 3: Load ordered active topics from M1 -----------------------
        topics = self.course_repo.list_course_topics(course_id, active_only=True)
        total_topics = len(topics)

        if total_topics == 0:
            return LearningPathResponse(
                course_id=course_id,
                student_id=student_id,
                total_topics=0,
                unlocked_count=0,
                completed_count=0,
                completion_percentage=0.0,
                path=[],
            )

        # --- Step 4: Get mastery parameters and build calculator --------------
        params = self.adaptive_repo.get_course_settings(course_id)
        calculator = MasteryCalculator.from_parameters(params)

        # --- Step 5: Compute mastery per topic --------------------------------
        # Build mapping: topic_id -> (score, level)
        mastery_map: dict[int, tuple[float, str]] = {}
        for topic in topics:
            responses = self.adaptive_repo.get_student_topic_responses(student_id, topic.id)
            result = calculator.calculate_mastery(responses)
            mastery_map[topic.id] = (result.score, result.level)

        # --- Step 6: Collect prerequisite IDs per topic -----------------------
        prereq_map: dict[int, list[int]] = {}
        for topic in topics:
            prereq_map[topic.id] = self.course_repo.get_prerequisites_for_topic(topic.id)

        # --- Phase 1: Prerequisite-aware unlocking ----------------------------
        # A topic is unlocked if it has no prerequisites OR all prerequisites are Proficient.
        unlock_map: dict[int, tuple[bool, str | None]] = {}
        for topic in topics:
            prereqs = prereq_map[topic.id]
            if not prereqs:
                unlock_map[topic.id] = (True, None)
            else:
                locked_reason: str | None = None
                all_met = True
                for prereq_id in prereqs:
                    prereq_level = mastery_map.get(prereq_id, (0.0, "Not Assessed"))[1]
                    if prereq_level != _PROFICIENT:
                        # Find the topic title for a human-readable message
                        prereq_title = self._get_topic_title(topics, prereq_id)
                        locked_reason = (
                            f"Prerequisite '{prereq_title}' not yet Proficient "
                            f"(current level: {prereq_level})"
                        )
                        all_met = False
                        break
                unlock_map[topic.id] = (all_met, locked_reason)

        # --- Phase 2: Pedagogical recommendation (M3 engine) -----------------
        # Collect unlocked, non-Proficient candidates for the recommender
        engine_prereqs: dict[int, set[int]] = {tid: set(pids) for tid, pids in prereq_map.items()}
        candidate_inputs: list[TopicRecommendationInput] = []
        for topic in topics:
            is_unlocked, _ = unlock_map[topic.id]
            score, level = mastery_map[topic.id]
            if is_unlocked and level != _PROFICIENT:
                candidate_inputs.append(
                    TopicRecommendationInput(
                        topic_id=topic.id,
                        name=topic.title,
                        mastery_level=level,
                        score=score,
                        prerequisites=tuple(prereq_map[topic.id]),
                    )
                )

        # Call the M3 recommendation engine (max_recommendations=None -> all candidates ranked)
        recommendations = self.strategy_creator.recommend(
            topics=candidate_inputs,
            prerequisites=engine_prereqs,
            max_recommendations=None,
        )
        # Build quick lookup: recommended topic_id -> rationale
        recommended_map: dict[int, str] = {r.topic_id: r.rationale for r in recommendations}

        # --- Step 7: Assemble TopicPathItem list ------------------------------
        path_items: list[TopicPathItem] = []
        completed_count = 0
        unlocked_count = 0

        for topic in topics:
            score, level = mastery_map[topic.id]
            is_unlocked, locked_reason = unlock_map[topic.id]
            is_recommended = topic.id in recommended_map
            rationale = recommended_map.get(topic.id)

            if is_unlocked:
                unlocked_count += 1
            if level == _PROFICIENT:
                completed_count += 1

            path_items.append(
                TopicPathItem(
                    topic_id=topic.id,
                    title=topic.title,
                    description=topic.description,
                    order_index=topic.order_index,
                    status=level,
                    score=score,
                    is_unlocked=is_unlocked,
                    is_recommended=is_recommended,
                    locked_reason=locked_reason,
                    prerequisite_topic_ids=prereq_map[topic.id],
                    rationale=rationale,
                )
            )

        completion_percentage = (
            (completed_count / total_topics * 100.0) if total_topics > 0 else 0.0
        )

        return LearningPathResponse(
            course_id=course_id,
            student_id=student_id,
            total_topics=total_topics,
            unlocked_count=unlocked_count,
            completed_count=completed_count,
            completion_percentage=round(completion_percentage, 2),
            path=path_items,
        )

    # =========================================================================
    # Private Helpers
    # =========================================================================

    @staticmethod
    def _get_topic_title(topics: list, topic_id: int) -> str:
        """Return the title of a topic by its ID, or fall back to the ID string."""
        for t in topics:
            if t.id == topic_id:
                return t.title
        return str(topic_id)


# ---------------------------------------------------------------------------
# Dependency Injection Factory
# ---------------------------------------------------------------------------

_global_learning_path_service: LearningPathService | None = None


def get_learning_path_service() -> LearningPathService:
    """FastAPI dependency provider for LearningPathService singleton."""
    global _global_learning_path_service
    if _global_learning_path_service is None:
        _global_learning_path_service = LearningPathService()
    return _global_learning_path_service
