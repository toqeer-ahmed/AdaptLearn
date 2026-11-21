"""API router for Module 2: Quiz & Assessment Engine endpoints (FR-08 through FR-14).

Requirements Traceability:
- FR-08: Question authoring, updating, and detail viewing.
- FR-09: Soft-delete for answered questions.
- FR-10: Quiz creation, question assignment, and publication.
- FR-11: Student-safe quiz retrieval for active assessments.
- FR-12: On-demand topic practice quiz generation.
- FR-13: Single-transaction attempt submission & automated scoring.
- FR-14: Detailed attempt results and feedback display.
- NFR-05: Server-side RBAC enforced via CurrentUser and require_role.
- NFR-06: Student privacy protection on attempt results.
- NFR-14: Standardized, defensive JSON responses.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status

from app.core.auth import CurrentUser, get_current_user, require_role
from app.schemas.quiz import (
    AttemptResultResponse,
    PracticeQuizRequest,
    QuestionCreate,
    QuestionResponse,
    QuestionStudentSafe,
    QuestionUpdate,
    QuizAttemptSubmitRequest,
    QuizCreate,
    QuizResponse,
    QuizStudentSafeResponse,
    QuizSummaryResponse,
)
from app.services.quiz_service import QuizService, get_quiz_service

router = APIRouter()


# =============================================================================
# Question Bank Endpoints (FR-08, FR-09)
# =============================================================================

@router.post(
    "/courses/{course_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Course Question",
    tags=["Question Bank"],
)
def create_question(
    course_id: int,
    payload: QuestionCreate,
    topic_id: Annotated[Optional[int], Query(description="Associated topic ID")] = None,
    current_user: CurrentUser = Depends(require_role(["instructor"])),
    service: QuizService = Depends(get_quiz_service),
) -> QuestionResponse:
    """Create a new multiple-choice question in the course question bank (FR-08)."""
    return service.create_question(
        course_id=course_id,
        payload=payload,
        instructor_id=current_user.user_id,
        topic_id=topic_id,
    )


@router.patch(
    "/questions/{question_id}",
    response_model=QuestionResponse,
    summary="Update Question",
    tags=["Question Bank"],
)
def update_question(
    question_id: int,
    payload: QuestionUpdate,
    current_user: CurrentUser = Depends(require_role(["instructor"])),
    service: QuizService = Depends(get_quiz_service),
) -> QuestionResponse:
    """Update question statement, options, difficulty, or active status (FR-08)."""
    return service.update_question(
        question_id=question_id,
        payload=payload,
        instructor_id=current_user.user_id,
    )


@router.delete(
    "/questions/{question_id}",
    summary="Delete / Soft-Delete Question",
    tags=["Question Bank"],
)
def delete_question(
    question_id: int,
    current_user: CurrentUser = Depends(require_role(["instructor"])),
    service: QuizService = Depends(get_quiz_service),
) -> dict:
    """Delete a question or soft-delete it if historical attempt answers exist (FR-09)."""
    return service.delete_question(
        question_id=question_id,
        instructor_id=current_user.user_id,
    )


@router.get(
    "/questions/{question_id}",
    response_model=QuestionResponse,
    summary="Get Question Details",
    tags=["Question Bank"],
)
def get_question(
    question_id: int,
    current_user: CurrentUser = Depends(require_role(["instructor"])),
    service: QuizService = Depends(get_quiz_service),
) -> QuestionResponse:
    """Retrieve question with correct answer and explanation (Instructor only)."""
    return service.get_question(
        question_id=question_id,
        user_id=current_user.user_id,
        role=current_user.role,
    )


@router.get(
    "/courses/{course_id}/questions",
    response_model=list[QuestionResponse],
    summary="List Course Questions",
    tags=["Question Bank"],
)
def list_course_questions(
    course_id: int,
    topic_id: Annotated[Optional[int], Query(description="Filter by topic ID")] = None,
    current_user: CurrentUser = Depends(require_role(["instructor"])),
    service: QuizService = Depends(get_quiz_service),
) -> list[QuestionResponse]:
    """List all questions authored for a course (FR-08)."""
    return service.list_course_questions(
        course_id=course_id,
        topic_id=topic_id,
        instructor_id=current_user.user_id,
    )


# =============================================================================
# Quiz Management & Taking Endpoints (FR-10, FR-11, FR-12)
# =============================================================================

@router.post(
    "/courses/{course_id}/quizzes",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Quiz",
    tags=["Quizzes"],
)
def create_quiz(
    course_id: int,
    payload: QuizCreate,
    current_user: CurrentUser = Depends(require_role(["instructor"])),
    service: QuizService = Depends(get_quiz_service),
) -> QuizResponse:
    """Create a new quiz from the question bank (FR-10)."""
    return service.create_quiz(
        course_id=course_id,
        payload=payload,
        instructor_id=current_user.user_id,
    )


@router.post(
    "/quizzes/{quiz_id}/publish",
    response_model=QuizResponse,
    summary="Publish / Unpublish Quiz",
    tags=["Quizzes"],
)
def publish_quiz(
    quiz_id: int,
    is_published: Annotated[bool, Query(description="Publication status")] = True,
    current_user: CurrentUser = Depends(require_role(["instructor"])),
    service: QuizService = Depends(get_quiz_service),
) -> QuizResponse:
    """Publish or unpublish a quiz for student attempts (FR-10)."""
    return service.publish_quiz(
        quiz_id=quiz_id,
        is_published=is_published,
        instructor_id=current_user.user_id,
    )


@router.get(
    "/courses/{course_id}/quizzes",
    response_model=list[QuizSummaryResponse],
    summary="List Course Quizzes",
    tags=["Quizzes"],
)
def list_course_quizzes(
    course_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    service: QuizService = Depends(get_quiz_service),
) -> list[QuizSummaryResponse]:
    """List quizzes in a course (enrolled students see published only) (FR-10)."""
    return service.list_course_quizzes(
        course_id=course_id,
        user_id=current_user.user_id,
        role=current_user.role,
    )


@router.get(
    "/quizzes/{quiz_id}",
    response_model=QuizStudentSafeResponse,
    summary="Get Student-Safe Quiz for Attempt",
    tags=["Quizzes"],
)
def get_quiz_for_taking(
    quiz_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    service: QuizService = Depends(get_quiz_service),
) -> QuizStudentSafeResponse:
    """Retrieve quiz questions with correct answers stripped for assessment taking (FR-11)."""
    return service.get_quiz_for_taking(
        quiz_id=quiz_id,
        student_id=current_user.user_id,
    )


@router.post(
    "/courses/{course_id}/topics/{topic_id}/practice-quiz",
    response_model=QuizStudentSafeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start Topic Practice Quiz",
    tags=["Quizzes"],
)
def start_topic_practice_quiz(
    course_id: int,
    topic_id: int,
    question_count: Annotated[int, Query(ge=1, le=20, description="Desired question count")] = 5,
    current_user: CurrentUser = Depends(require_role(["student"])),
    service: QuizService = Depends(get_quiz_service),
) -> QuizStudentSafeResponse:
    """Generate an on-demand dynamic practice quiz assembled from active topic questions (FR-12)."""
    return service.create_practice_quiz(
        course_id=course_id,
        payload=PracticeQuizRequest(topic_id=topic_id, question_count=question_count),
        student_id=current_user.user_id,
    )


# =============================================================================
# Attempt Submission & Grading Endpoints (FR-13, FR-14)
# =============================================================================

@router.post(
    "/quizzes/{quiz_id}/attempts",
    response_model=AttemptResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Quiz Attempt",
    tags=["Assessment & Grading"],
)
def submit_quiz_attempt(
    quiz_id: int,
    payload: QuizAttemptSubmitRequest,
    current_user: CurrentUser = Depends(require_role(["student"])),
    service: QuizService = Depends(get_quiz_service),
) -> AttemptResultResponse:
    """Submit quiz answers with atomic grading and mastery updates (FR-13, NFR-08)."""
    return service.submit_quiz_attempt(
        quiz_id=quiz_id,
        student_id=current_user.user_id,
        payload=payload,
    )


@router.get(
    "/attempts/{attempt_id}",
    response_model=AttemptResultResponse,
    summary="Get Attempt Results",
    tags=["Assessment & Grading"],
)
def get_attempt_result(
    attempt_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    service: QuizService = Depends(get_quiz_service),
) -> AttemptResultResponse:
    """View detailed attempt results, score breakdown, and explanations (FR-14, NFR-06)."""
    return service.get_attempt_result(
        attempt_id=attempt_id,
        user_id=current_user.user_id,
        role=current_user.role,
    )
