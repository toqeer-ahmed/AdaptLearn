"""FastAPI router for Module 4: Personalized Learning Paths (AdaptLearn M4).

Requirements Traceability:
- FR-18: Return ordered, prerequisite-aware topic list with mastery and unlock status.
- FR-19: Include M3 engine recommendation tagging with rationale.
- FR-20: Cold-start support for students with no prior attempt history.
- FR-25: Defensive Pydantic schema responses and REST contracts.
- Decision 5: Instructor can supply ?student_id to view a specific student's path.
- NFR-06: Students may only view their own path.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.auth import CurrentUser, get_current_user
from app.schemas.learning_path import LearningPathResponse
from app.services.learning_path_service import (
    LearningPathService,
    get_learning_path_service,
)

router = APIRouter()


@router.get(
    "/courses/{course_id}/learning-path",
    response_model=LearningPathResponse,
    summary="Get personalized learning path for a course",
    description=(
        "Returns an ordered, prerequisite-aware personalized learning path for a student "
        "in the specified course. Topics are annotated with mastery status, unlock state, "
        "and pedagogical recommendations from the M3 engine.\n\n"
        "**Authorization:**\n"
        "- Student: must be enrolled in the course; can only view their own path.\n"
        "- Instructor: must own the course; may supply `?student_id=<id>` to view "
        "a specific student's path (Decision 5)."
    ),
    tags=["Learning Paths"],
)
def get_learning_path(
    course_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[LearningPathService, Depends(get_learning_path_service)],
    student_id: Annotated[
        int | None,
        Query(
            description=(
                "Optional student ID (instructor only). "
                "When omitted, defaults to the authenticated user's ID."
            )
        ),
    ] = None,
) -> LearningPathResponse:
    """Compute and return the personalized learning path.

    Args:
        course_id: Path parameter -- the course to generate the path for.
        current_user: Authenticated user principal injected by FastAPI.
        service: LearningPathService instance injected by FastAPI.
        student_id: Optional query param -- instructor-only override for target student.

    Returns:
        LearningPathResponse with ordered TopicPathItem list and summary statistics.
    """
    # Resolve target student: instructor may pass ?student_id; student defaults to self
    target_student_id = student_id if student_id is not None else current_user.user_id

    return service.get_learning_path(
        course_id=course_id,
        student_id=target_student_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )
