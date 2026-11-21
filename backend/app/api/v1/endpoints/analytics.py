"""FastAPI router endpoints for Instructor Analytics (AdaptLearn M5).

Requirements Traceability:
- FR-22: View enrolled students with their mastery level in each topic (GET /courses/{id}/analytics/student-roster).
- FR-23: View number of students at each mastery level per topic (GET /courses/{id}/analytics/mastery-distribution).
- FR-24: View question answering statistics and correct percentage (GET /courses/{id}/analytics/questions).
- FR-03 & TC-03-1: Enforce instructor-only access control.
- TC-22-2: Enforce course-ownership authorization.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import CurrentUser, get_current_user
from app.repositories.progress_repository import (
    ProgressRepository,
    get_progress_repository,
)
from app.schemas.analytics import (
    CourseQuestionStatsResponse,
    MasteryDistributionResponse,
    StudentRosterResponse,
)
from app.services.analytics_service import AnalyticsService, get_analytics_service

router = APIRouter()


def _verify_instructor_course_access(
    course_id: int,
    user: CurrentUser,
    repo: ProgressRepository,
) -> None:
    """Enforce server-side instructor role and course ownership rules (TC-03-1, TC-22-2)."""
    if user.role != "instructor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Student cannot call instructor endpoints (TC-03-1)",
        )
    if not repo.is_course_owner(course_id=course_id, instructor_id=user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Instructor does not own this course (TC-22-2)",
        )


@router.get(
    "/courses/{id}/analytics/mastery-distribution",
    response_model=MasteryDistributionResponse,
    summary="Get Course Topic Mastery Distribution",
    tags=["Instructor Analytics"],
)
def get_course_mastery_distribution(
    id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    repo: Annotated[ProgressRepository, Depends(get_progress_repository)],
) -> MasteryDistributionResponse:
    """Retrieve aggregated counts of students at each mastery level for all course topics (FR-23)."""
    _verify_instructor_course_access(course_id=id, user=current_user, repo=repo)
    return service.get_mastery_distribution(course_id=id)


@router.get(
    "/courses/{id}/analytics/student-roster",
    response_model=StudentRosterResponse,
    summary="Get Student Roster Mastery Matrix",
    tags=["Instructor Analytics"],
)
def get_course_student_roster(
    id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    repo: Annotated[ProgressRepository, Depends(get_progress_repository)],
) -> StudentRosterResponse:
    """Retrieve enrolled student roster with per-topic mastery scores (FR-22)."""
    _verify_instructor_course_access(course_id=id, user=current_user, repo=repo)
    return service.get_student_roster(course_id=id)


@router.get(
    "/courses/{id}/analytics/questions",
    response_model=CourseQuestionStatsResponse,
    summary="Get Course Question Performance Statistics",
    tags=["Instructor Analytics"],
)
def get_course_question_statistics(
    id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
    repo: Annotated[ProgressRepository, Depends(get_progress_repository)],
) -> CourseQuestionStatsResponse:
    """Retrieve question answering frequency and correct answer percentage (FR-24)."""
    _verify_instructor_course_access(course_id=id, user=current_user, repo=repo)
    return service.get_question_stats(course_id=id)
