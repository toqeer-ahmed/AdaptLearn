"""FastAPI router endpoints for Student Progress and History (AdaptLearn M5).

Requirements Traceability:
- FR-21: Student dashboard endpoint (GET /courses/{id}/progress).
- FR-15: Student attempt history endpoint (GET /courses/{id}/attempts).
- NFR-05: Server-side role & ownership access control.
- NFR-06: Student privacy protection — students cannot access other students' records.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import CurrentUser, get_current_user
from app.repositories.progress_repository import (
    ProgressRepository,
    get_progress_repository,
)
from app.schemas.progress import (
    AttemptHistoryResponse,
    StudentProgressResponse,
)
from app.services.progress_service import ProgressService, get_progress_service

router = APIRouter()


@router.get(
    "/courses/{id}/progress",
    response_model=StudentProgressResponse,
    summary="Get Student Course Progress Dashboard",
    tags=["Progress & Analytics"],
)
def get_student_course_progress(
    id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[ProgressService, Depends(get_progress_service)],
    repo: Annotated[ProgressRepository, Depends(get_progress_repository)],
    student_id: Annotated[int | None, Query(description="Target student ID (defaults to current user)")] = None,
) -> StudentProgressResponse:
    """Retrieve consolidated student progress for an enrolled course (FR-21).

    Authorization (NFR-05, NFR-06):
    - Students can only view their own progress for enrolled courses.
    - Instructors can view student progress for courses they own.
    """
    target_student_id = student_id if student_id is not None else current_user.user_id

    if current_user.role == "student":
        # Privacy check: Student A cannot view Student B (NFR-06)
        if target_student_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Student cannot access another student's progress data",
            )
        # Enrollment check (NFR-05)
        if not repo.is_student_enrolled(student_id=target_student_id, course_id=id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Student is not enrolled in this course",
            )
    elif current_user.role == "instructor":
        # Ownership check: Instructor must own this course (NFR-06)
        if not repo.is_course_owner(course_id=id, instructor_id=current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Instructor does not own this course",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Unauthorized role",
        )

    return service.get_student_progress(student_id=target_student_id, course_id=id)


@router.get(
    "/courses/{id}/attempts",
    response_model=AttemptHistoryResponse,
    summary="Get Student Attempt History",
    tags=["Progress & Analytics"],
)
def get_student_attempt_history(
    id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[ProgressService, Depends(get_progress_service)],
    repo: Annotated[ProgressRepository, Depends(get_progress_repository)],
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=50, description="Items per page")] = 10,
    student_id: Annotated[int | None, Query(description="Target student ID (defaults to current user)")] = None,
) -> AttemptHistoryResponse:
    """Retrieve paginated quiz attempt history for a student in a course (FR-15)."""
    target_student_id = student_id if student_id is not None else current_user.user_id

    if current_user.role == "student":
        if target_student_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Student cannot access another student's attempt history",
            )
        if not repo.is_student_enrolled(student_id=target_student_id, course_id=id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Student is not enrolled in this course",
            )
    elif current_user.role == "instructor":
        if not repo.is_course_owner(course_id=id, instructor_id=current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Instructor does not own this course",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Unauthorized role",
        )

    return service.get_attempt_history(
        student_id=target_student_id,
        course_id=id,
        page=page,
        page_size=page_size,
    )
