"""FastAPI router endpoints for Course, Topic, Prerequisite, and Enrollment Management (AdaptLearn M1).

Requirements Traceability:
- FR-04: Course creation, unique course codes, instructor ownership.
- FR-05: Course lifecycle, updates, and archiving.
- FR-06: Topic creation, retrieval, sequential ordering.
- FR-07: Sequential topic reordering with transactional integrity.
- FR-08: Topic prerequisite relationships and dependencies.
- FR-09: Prerequisite graph integrity and cycle detection.
- FR-10: Student course enrollment and discovery.
- Decisions:
  - D1: Course code validation, uppercase normalization, uniqueness.
  - D2: Topic deletion restriction if referenced by quiz questions.
  - D3: Archiving lifecycle, read-only policy for archived courses.
  - D6: Adoption of existing course_enrollments schema without regression.
  - D7: Dual-source course ownership synchronization with ProgressRepository.
"""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.core.auth import CurrentUser, get_current_user, require_role
from app.schemas.course import (
    CourseCreate,
    CourseListResponse,
    CourseResponse,
    CourseUpdate,
    EnrollmentRequest,
    EnrollmentResponse,
    TopicCreate,
    TopicListResponse,
    TopicPrerequisiteCreate,
    TopicPrerequisiteResponse,
    TopicReorderRequest,
    TopicResponse,
    TopicUpdate,
    UserEnrollmentsResponse,
)
from app.services.course_service import CourseService, get_course_service

router = APIRouter()


# =============================================================================
# Course Management Endpoints (FR-04, FR-05, Decisions D1, D3, D7)
# =============================================================================


@router.post(
    "/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course (FR-04, Decision D1)",
    tags=["Courses & Topics"],
)
def create_course(
    payload: CourseCreate,
    current_user: Annotated[CurrentUser, Depends(require_role(["instructor"]))],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> CourseResponse:
    """Create a new course authored by the authenticated instructor."""
    return service.create_course(
        payload=payload,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )


@router.get(
    "/courses",
    response_model=CourseListResponse,
    summary="List courses with optional filters (FR-04, FR-07, Decision D3)",
    tags=["Courses & Topics"],
)
def list_courses(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[CourseService, Depends(get_course_service)],
    instructor_id: Annotated[
        int | None, Query(description="Filter courses by instructor ID")
    ] = None,
    is_archived: Annotated[
        bool | None, Query(description="Filter courses by archive status")
    ] = None,
    enrolled: Annotated[bool, Query(description="Filter only courses enrolled by student")] = False,
) -> CourseListResponse:
    """List available or enrolled courses."""
    if enrolled and current_user.role == "student":
        enrollments = service.get_student_enrollments(
            student_id=current_user.user_id,
            current_user_id=current_user.user_id,
            current_user_role=current_user.role,
        )
        return CourseListResponse(courses=enrollments.enrolled_courses, total=enrollments.total)

    include_archived = is_archived is True
    return service.list_courses(
        instructor_id=instructor_id,
        include_archived=include_archived,
    )


@router.get(
    "/courses/enrolled",
    response_model=UserEnrollmentsResponse,
    summary="List courses enrolled by the current authenticated student (FR-10)",
    tags=["Courses & Topics"],
)
@router.get(
    "/users/me/enrollments",
    response_model=UserEnrollmentsResponse,
    summary="List enrolled courses for current student",
    tags=["Courses & Topics"],
)
def get_my_enrolled_courses(
    current_user: Annotated[CurrentUser, Depends(require_role(["student"]))],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> UserEnrollmentsResponse:
    """Return all courses that the authenticated student is currently enrolled in."""
    return service.get_student_enrollments(
        student_id=current_user.user_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )


@router.get(
    "/courses/{course_id}",
    response_model=CourseResponse,
    summary="Get course details by ID (FR-04, Decision D3)",
    tags=["Courses & Topics"],
)
def get_course(
    course_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> CourseResponse:
    """Retrieve full details of a course by its identifier."""
    return service.get_course(
        course_id=course_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )


@router.put(
    "/courses/{course_id}",
    response_model=CourseResponse,
    summary="Update course metadata (FR-05, Decision D3)",
    tags=["Courses & Topics"],
)
@router.patch(
    "/courses/{course_id}",
    response_model=CourseResponse,
    summary="Partially update course metadata (FR-05, Decision D3)",
    tags=["Courses & Topics"],
)
def update_course(
    course_id: int,
    payload: CourseUpdate,
    current_user: Annotated[CurrentUser, Depends(require_role(["instructor"]))],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> CourseResponse:
    """Update title, description, or archive status of an owned course."""
    return service.update_course(
        course_id=course_id,
        payload=payload,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )


@router.post(
    "/courses/{course_id}/archive",
    response_model=CourseResponse,
    summary="Archive a course (FR-05, Decision D3)",
    tags=["Courses & Topics"],
)
def archive_course(
    course_id: int,
    current_user: Annotated[CurrentUser, Depends(require_role(["instructor"]))],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> CourseResponse:
    """Archive a course, rendering it read-only and disallowing new enrollments."""
    return service.archive_course(
        course_id=course_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )


@router.post(
    "/courses/{course_id}/publish",
    response_model=CourseResponse,
    summary="Publish / unarchive a course (FR-05, Decision D3)",
    tags=["Courses & Topics"],
)
@router.post(
    "/courses/{course_id}/unarchive",
    response_model=CourseResponse,
    summary="Unarchive a course",
    tags=["Courses & Topics"],
)
def publish_course(
    course_id: int,
    current_user: Annotated[CurrentUser, Depends(require_role(["instructor"]))],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> CourseResponse:
    """Unarchive / publish a course, making it active for modifications and enrollment."""
    return service.publish_course(
        course_id=course_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )


# =============================================================================
# Topic Management Endpoints (FR-06, FR-07, Decision D2, D3)
# =============================================================================


@router.post(
    "/courses/{course_id}/topics",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a topic to a course (FR-06, Decision D3)",
    tags=["Courses & Topics"],
)
def create_topic(
    course_id: int,
    payload: TopicCreate,
    current_user: Annotated[CurrentUser, Depends(require_role(["instructor"]))],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> TopicResponse:
    """Add a topic to an active course owned by the authenticated instructor."""
    return service.create_topic(
        course_id=course_id,
        payload=payload,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )


@router.get(
    "/courses/{course_id}/topics",
    response_model=TopicListResponse,
    summary="List topics in sequential order (FR-06, Decision D3)",
    tags=["Courses & Topics"],
)
def list_course_topics(
    course_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[CourseService, Depends(get_course_service)],
    active_only: Annotated[bool, Query(description="Filter active topics only")] = False,
) -> TopicListResponse:
    """Retrieve all topics in a course ordered by sequential order_index."""
    return service.list_course_topics(
        course_id=course_id,
        active_only=active_only,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )


@router.put(
    "/courses/{course_id}/topics/order",
    response_model=TopicListResponse,
    summary="Batch reorder course topics (FR-07, Decision D3)",
    tags=["Courses & Topics"],
)
@router.put(
    "/courses/{course_id}/topics/reorder",
    response_model=TopicListResponse,
    summary="Batch reorder course topics atomically",
    tags=["Courses & Topics"],
)
def reorder_topics(
    course_id: int,
    payload: TopicReorderRequest,
    current_user: Annotated[CurrentUser, Depends(require_role(["instructor"]))],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> TopicListResponse:
    """Atomically update sequential ordering of topics within an owned course."""
    return service.reorder_topics(
        course_id=course_id,
        payload=payload,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )


@router.get(
    "/courses/{course_id}/topics/{topic_id}",
    response_model=TopicResponse,
    summary="Get topic details by ID",
    tags=["Courses & Topics"],
)
@router.get(
    "/topics/{topic_id}",
    response_model=TopicResponse,
    summary="Get topic details by ID (Direct)",
    tags=["Courses & Topics"],
)
def get_topic(
    topic_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[CourseService, Depends(get_course_service)],
    course_id: int | None = None,
) -> TopicResponse:
    """Retrieve details of a single topic by ID."""
    return service.get_topic(topic_id=topic_id)


@router.put(
    "/courses/{course_id}/topics/{topic_id}",
    response_model=TopicResponse,
    summary="Update topic details",
    tags=["Courses & Topics"],
)
@router.put(
    "/topics/{topic_id}",
    response_model=TopicResponse,
    summary="Update topic details (Direct)",
    tags=["Courses & Topics"],
)
@router.patch(
    "/courses/{course_id}/topics/{topic_id}",
    response_model=TopicResponse,
    summary="Partially update topic details",
    tags=["Courses & Topics"],
)
@router.patch(
    "/topics/{topic_id}",
    response_model=TopicResponse,
    summary="Partially update topic details (Direct)",
    tags=["Courses & Topics"],
)
def update_topic(
    topic_id: int,
    payload: TopicUpdate,
    current_user: Annotated[CurrentUser, Depends(require_role(["instructor"]))],
    service: Annotated[CourseService, Depends(get_course_service)],
    course_id: int | None = None,
) -> TopicResponse:
    """Update topic properties in an owned course."""
    return service.update_topic(
        topic_id=topic_id,
        payload=payload,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )


@router.delete(
    "/courses/{course_id}/topics/{topic_id}",
    summary="Delete a topic (FR-06, Decision D2, Decision D3)",
    tags=["Courses & Topics"],
)
@router.delete(
    "/topics/{topic_id}",
    summary="Delete a topic (Direct)",
    tags=["Courses & Topics"],
)
def delete_topic(
    topic_id: int,
    current_user: Annotated[CurrentUser, Depends(require_role(["instructor"]))],
    service: Annotated[CourseService, Depends(get_course_service)],
    course_id: int | None = None,
) -> dict[str, str]:
    """Delete a topic from an owned course if no quiz questions reference it."""
    return service.delete_topic(
        topic_id=topic_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )


# =============================================================================
# Prerequisite Management Endpoints (FR-08, FR-09)
# =============================================================================


@router.post(
    "/courses/{course_id}/topics/{topic_id}/prerequisites",
    response_model=TopicPrerequisiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a prerequisite to a topic (FR-08, FR-09)",
    tags=["Courses & Topics"],
)
@router.post(
    "/topics/{topic_id}/prerequisites",
    response_model=TopicPrerequisiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a prerequisite to a topic (Direct)",
    tags=["Courses & Topics"],
)
def add_prerequisite(
    topic_id: int,
    payload: TopicPrerequisiteCreate,
    current_user: Annotated[CurrentUser, Depends(require_role(["instructor"]))],
    service: Annotated[CourseService, Depends(get_course_service)],
    course_id: int | None = None,
) -> TopicPrerequisiteResponse:
    """Add a directed prerequisite edge between topics of the same course."""
    return service.add_prerequisite(
        topic_id=topic_id,
        prerequisite_topic_id=payload.prerequisite_topic_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )


@router.delete(
    "/courses/{course_id}/topics/{topic_id}/prerequisites/{prerequisite_id}",
    summary="Remove a prerequisite relationship (FR-08)",
    tags=["Courses & Topics"],
)
@router.delete(
    "/topics/{topic_id}/prerequisites/{prerequisite_id}",
    summary="Remove a prerequisite relationship (Direct)",
    tags=["Courses & Topics"],
)
def remove_prerequisite(
    topic_id: int,
    prerequisite_id: int,
    current_user: Annotated[CurrentUser, Depends(require_role(["instructor"]))],
    service: Annotated[CourseService, Depends(get_course_service)],
    course_id: int | None = None,
) -> dict[str, str]:
    """Remove a directed prerequisite edge from a topic in an owned course."""
    return service.remove_prerequisite(
        topic_id=topic_id,
        prerequisite_topic_id=prerequisite_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )


# =============================================================================
# Enrollment Management Endpoints (FR-10, Decision D6, NFR-06)
# =============================================================================


@router.post(
    "/courses/{course_id}/enroll",
    response_model=EnrollmentResponse,
    summary="Enroll authenticated student into a course (FR-10, Decision D6)",
    tags=["Courses & Topics"],
)
def enroll_in_course(
    course_id: int,
    current_user: Annotated[CurrentUser, Depends(require_role(["student"]))],
    service: Annotated[CourseService, Depends(get_course_service)],
    payload: Annotated[EnrollmentRequest | None, Body()] = None,
) -> EnrollmentResponse:
    """Enroll the authenticated student into an active course."""
    course_code = payload.course_code if payload is not None else None
    return service.enroll_student(
        course_id=course_id,
        student_id=current_user.user_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
        course_code=course_code,
    )


@router.get(
    "/courses/{course_id}/enrollment",
    response_model=EnrollmentResponse,
    summary="Check enrollment status of the current user in a course (FR-10)",
    tags=["Courses & Topics"],
)
def check_course_enrollment(
    course_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> EnrollmentResponse:
    """Verify if the authenticated user is enrolled in the specified course."""
    enrollment = service.course_repo.get_enrollment(
        student_id=current_user.user_id,
        course_id=course_id,
    )
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {current_user.user_id} is not enrolled in course {course_id}",
        )
    return EnrollmentResponse(
        id=enrollment.id,
        student_id=enrollment.student_id,
        course_id=enrollment.course_id,
    )


@router.get(
    "/students/{student_id}/enrollments",
    response_model=UserEnrollmentsResponse,
    summary="List courses enrolled by student ID (FR-10, Privacy NFR-06)",
    tags=["Courses & Topics"],
)
def get_student_enrollments(
    student_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> UserEnrollmentsResponse:
    """Retrieve enrolled courses for a student, strictly enforcing privacy bounds."""
    return service.get_student_enrollments(
        student_id=student_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )


@router.get(
    "/courses/{course_id}/students",
    response_model=list[int],
    summary="List student IDs enrolled in course (Instructor Owner Only)",
    tags=["Courses & Topics"],
)
@router.get(
    "/courses/{course_id}/enrollments",
    response_model=list[int],
    summary="List student IDs enrolled in course (Alias)",
    tags=["Courses & Topics"],
)
def get_course_enrolled_students(
    course_id: int,
    current_user: Annotated[CurrentUser, Depends(require_role(["instructor"]))],
    service: Annotated[CourseService, Depends(get_course_service)],
) -> list[int]:
    """Retrieve roster of student IDs enrolled in an owned course."""
    return service.get_course_students(
        course_id=course_id,
        current_user_id=current_user.user_id,
        current_user_role=current_user.role,
    )
