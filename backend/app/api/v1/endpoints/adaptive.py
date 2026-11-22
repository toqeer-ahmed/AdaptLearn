"""FastAPI router endpoints for the Adaptive Learning Engine (AdaptLearn M3).

Requirements Traceability:
- FR-16: Recalculate mastery across attempt topics (POST /courses/{id}/recalculate-mastery).
- FR-18 & FR-19: Get ordered topic recommendations (GET /courses/{id}/recommendations).
- FR-20: View and update adaptive parameters per course (GET/PUT /courses/{id}/adaptive-settings).
- NFR-05 & NFR-15: Strict architectural layering (Router calls Service only).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.adaptive import (
    AdaptiveSettingsResponse,
    AdaptiveSettingsUpdate,
    AttemptMasteryRecalculateRequest,
    AttemptMasteryRecalculateResponse,
    RecommendationListResponse,
)
from app.services.adaptive_service import AdaptiveService, get_adaptive_service

router = APIRouter()


@router.get(
    "/courses/{id}/adaptive-settings",
    response_model=AdaptiveSettingsResponse,
    summary="Get Course Adaptive Parameters",
    tags=["Adaptive Engine"],
)
def get_course_adaptive_settings(
    id: int,
    service: Annotated[AdaptiveService, Depends(get_adaptive_service)],
) -> AdaptiveSettingsResponse:
    """Retrieve the adaptive learning parameters (N, weights, thresholds) for a course (FR-20)."""
    return service.get_course_settings(course_id=id)


@router.put(
    "/courses/{id}/adaptive-settings",
    response_model=AdaptiveSettingsResponse,
    summary="Update Course Adaptive Parameters",
    tags=["Adaptive Engine"],
)
def update_course_adaptive_settings(
    id: int,
    update: AdaptiveSettingsUpdate,
    service: Annotated[AdaptiveService, Depends(get_adaptive_service)],
) -> AdaptiveSettingsResponse:
    """Update adaptive parameters for a course; applies to future calculations (FR-20)."""
    try:
        return service.update_course_settings(course_id=id, update=update)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get(
    "/courses/{id}/recommendations",
    response_model=RecommendationListResponse,
    summary="Get Topic Recommendations",
    tags=["Adaptive Engine"],
)
def get_topic_recommendations(
    id: int,
    service: Annotated[AdaptiveService, Depends(get_adaptive_service)],
    limit: Annotated[int | None, Query(ge=1, description="Maximum recommendations to return")] = None,
) -> RecommendationListResponse:
    """Get ordered list of recommended topics with pedagogical rationale (FR-18, FR-19)."""
    return service.get_recommendations(course_id=id, limit=limit)


@router.post(
    "/courses/{id}/recalculate-mastery",
    response_model=AttemptMasteryRecalculateResponse,
    summary="Recalculate Attempt Mastery",
    tags=["Adaptive Engine"],
)
def recalculate_attempt_mastery(
    id: int,
    request: AttemptMasteryRecalculateRequest,
    service: Annotated[AdaptiveService, Depends(get_adaptive_service)],
) -> AttemptMasteryRecalculateResponse:
    """Recalculate student mastery across all attempt topics (FR-16, NFR-08)."""
    if request.course_id != id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path course_id ({id}) does not match body course_id ({request.course_id})",
        )
    try:
        return service.recalculate_attempt_mastery(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
