"""Application service for Quiz & Assessment Engine coordination (AdaptLearn M2).

Architecture & Layering:
Router -> Service -> Repository -> Database / ORM

Requirements Traceability:
- FR-08: MCQ question bank authoring and configuration.
- FR-09: Soft-delete enforcement on answered questions.
- FR-10: Quiz creation, question ordering, and publication.
- FR-11: Student-safe quiz retrieval omitting correct answers.
- FR-12: On-demand topic practice quiz assembly.
- FR-13: Single-transaction automated grading and attempt processing.
- FR-14: Detailed attempt results with score breakdown and feedback.
- NFR-05: Server-side RBAC verifying course ownership and student enrollment.
- NFR-06: Student privacy isolation.
- NFR-08: Transactional atomicity (attempt + answers + stats + adaptive updates).
- NFR-10: Deterministic scoring and calculation.
"""
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.engine.mastery_calculator import ResponseRecord
from app.models.adaptive import StudentTopicResponseModel
from app.models.progress import AttemptModel, QuestionStatsModel
from app.models.quiz import AttemptAnswerModel, QuestionModel
from app.repositories.adaptive_repository import AdaptiveRepository, get_adaptive_repository
from app.repositories.progress_repository import (
    AttemptRecord,
    ProgressRepository,
    get_progress_repository,
)
from app.repositories.quiz_repository import (
    AnswerRecordInput,
    QuestionRecord,
    QuestionRecordInput,
    QuizRecord,
    QuizRecordInput,
    QuizRepository,
    get_quiz_repository,
)
from app.schemas.quiz import (
    AttemptResultResponse,
    GradedAnswerResponse,
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
    QuizUpdate,
    TopicScoreBreakdown,
)


class QuizService:
    """Service orchestrating question bank management, quizzes, and atomic grading."""

    def __init__(
        self,
        quiz_repository: Optional[QuizRepository] = None,
        progress_repository: Optional[ProgressRepository] = None,
        adaptive_repository: Optional[AdaptiveRepository] = None,
        session_factory: Optional[Any] = None,
    ) -> None:
        self.quiz_repo = quiz_repository or get_quiz_repository()
        self.progress_repo = progress_repository or get_progress_repository()
        self.adaptive_repo = adaptive_repository or get_adaptive_repository()
        self.session_factory = session_factory or SessionLocal

    # -------------------------------------------------------------------------
    # Question Bank Management (FR-08, FR-09)
    # -------------------------------------------------------------------------

    def create_question(
        self,
        course_id: int,
        payload: QuestionCreate,
        instructor_id: int,
        topic_id: Optional[int] = None,
    ) -> QuestionResponse:
        """Create a question in a course question bank (FR-08, NFR-05)."""
        self._require_course_owner(course_id, instructor_id)

        target_topic_id = topic_id or 1  # Default topic if not specified
        record_input = QuestionRecordInput(
            course_id=course_id,
            topic_id=target_topic_id,
            statement=payload.statement,
            options=payload.options,
            correct_option_index=payload.correct_option_index,
            difficulty=payload.difficulty,
            explanation=payload.explanation,
        )
        saved = self.quiz_repo.create_question(record_input)
        return self._to_question_response(saved)

    def update_question(
        self,
        question_id: int,
        payload: QuestionUpdate,
        instructor_id: int,
    ) -> QuestionResponse:
        """Update an existing question (FR-08)."""
        existing = self.quiz_repo.get_question_by_id(question_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question with ID {question_id} not found",
            )
        self._require_course_owner(existing.course_id, instructor_id)

        updated = self.quiz_repo.update_question(
            question_id=question_id,
            statement=payload.statement,
            options=payload.options,
            correct_option_index=payload.correct_option_index,
            difficulty=payload.difficulty,
            explanation=payload.explanation,
            is_active=payload.is_active,
        )
        if updated is None:
            raise HTTPException(status_code=404, detail="Question update failed")
        return self._to_question_response(updated)

    def delete_question(self, question_id: int, instructor_id: int) -> dict[str, Any]:
        """Delete or soft-delete a question based on attempt history (FR-09)."""
        existing = self.quiz_repo.get_question_by_id(question_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question with ID {question_id} not found",
            )
        self._require_course_owner(existing.course_id, instructor_id)

        was_soft_deleted = self.quiz_repo.delete_question(question_id)
        if was_soft_deleted:
            return {
                "deleted": False,
                "soft_deleted": True,
                "is_active": False,
                "message": "Question deactivated due to existing student attempt history (FR-09).",
            }
        return {
            "deleted": True,
            "soft_deleted": False,
            "message": "Question permanently deleted.",
        }

    def get_question(self, question_id: int, user_id: int, role: str) -> QuestionResponse:
        """Retrieve full question details (Instructors only)."""
        q = self.quiz_repo.get_question_by_id(question_id)
        if q is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question with ID {question_id} not found",
            )
        if role.lower() == "instructor":
            self._require_course_owner(q.course_id, user_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Full question details are restricted to course instructors.",
            )
        return self._to_question_response(q)

    def list_course_questions(
        self,
        course_id: int,
        topic_id: Optional[int] = None,
        instructor_id: int = 1,
    ) -> list[QuestionResponse]:
        """List questions for a course question bank."""
        self._require_course_owner(course_id, instructor_id)
        questions = self.quiz_repo.get_course_questions(
            course_id=course_id, topic_id=topic_id, active_only=False
        )
        return [self._to_question_response(q) for q in questions]

    # -------------------------------------------------------------------------
    # Quiz Creation, Publishing & Presentation (FR-10, FR-11, FR-12)
    # -------------------------------------------------------------------------

    def create_quiz(
        self,
        course_id: int,
        payload: QuizCreate,
        instructor_id: int,
    ) -> QuizResponse:
        """Create a quiz with ordered question sequence (FR-10)."""
        self._require_course_owner(course_id, instructor_id)

        quiz_input = QuizRecordInput(
            course_id=course_id,
            title=payload.title,
            description=payload.description,
            topic_id=payload.topic_id,
            question_ids=payload.question_ids,
            is_published=payload.is_published,
            is_practice=payload.is_practice,
        )
        saved = self.quiz_repo.create_quiz(quiz_input)
        return self._to_quiz_response(saved)

    def publish_quiz(
        self,
        quiz_id: int,
        is_published: bool,
        instructor_id: int,
    ) -> QuizResponse:
        """Toggle quiz publication status (FR-10)."""
        existing = self.quiz_repo.get_quiz_by_id(quiz_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {quiz_id} not found",
            )
        self._require_course_owner(existing.course_id, instructor_id)

        if is_published and not existing.questions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish a quiz with zero questions.",
            )

        updated = self.quiz_repo.set_quiz_published(quiz_id, is_published=is_published)
        if updated is None:
            raise HTTPException(status_code=404, detail="Quiz not found")
        return self._to_quiz_response(updated)

    def get_quiz_for_taking(
        self,
        quiz_id: int,
        student_id: int,
    ) -> QuizStudentSafeResponse:
        """Retrieve student-safe quiz for assessment taking (FR-11)."""
        quiz = self.quiz_repo.get_quiz_by_id(quiz_id)
        if quiz is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {quiz_id} not found",
            )
        if not quiz.is_published:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quiz is currently unpublished and unavailable to students.",
            )
        self._require_student_enrollment(quiz.course_id, student_id)

        safe_questions = [
            QuestionStudentSafe(
                id=q.id,
                statement=q.statement,
                options=q.options,
            )
            for q in quiz.questions
            if q.is_active
        ]

        return QuizStudentSafeResponse(
            id=quiz.id,
            course_id=quiz.course_id,
            title=quiz.title,
            description=quiz.description,
            topic_id=quiz.topic_id,
            questions=safe_questions,
        )

    def list_course_quizzes(
        self,
        course_id: int,
        user_id: int,
        role: str,
    ) -> list[QuizSummaryResponse]:
        """List quizzes for a course, filtered by role and publication status."""
        is_instructor = role.lower() == "instructor"
        if is_instructor:
            self._require_course_owner(course_id, user_id)
            quizzes = self.quiz_repo.get_course_quizzes(course_id, published_only=False)
        else:
            self._require_student_enrollment(course_id, user_id)
            quizzes = self.quiz_repo.get_course_quizzes(course_id, published_only=True)

        return [
            QuizSummaryResponse(
                id=q.id,
                course_id=q.course_id,
                title=q.title,
                description=q.description,
                topic_id=q.topic_id,
                is_published=q.is_published,
                is_practice=q.is_practice,
                question_count=len(q.questions),
                created_at=q.created_at,
            )
            for q in quizzes
        ]

    def create_practice_quiz(
        self,
        course_id: int,
        payload: PracticeQuizRequest,
        student_id: int,
    ) -> QuizStudentSafeResponse:
        """Assemble an on-demand dynamic practice quiz from active topic questions (FR-12)."""
        self._require_student_enrollment(course_id, student_id)

        active_questions = self.quiz_repo.get_active_questions_by_topic(
            course_id=course_id, topic_id=payload.topic_id
        )
        if not active_questions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active questions available for topic {payload.topic_id}.",
            )

        selected = active_questions[: payload.question_count]
        quiz_input = QuizRecordInput(
            course_id=course_id,
            title=f"Practice Quiz: Topic {payload.topic_id}",
            description="On-demand topic mastery practice session.",
            topic_id=payload.topic_id,
            question_ids=[q.id for q in selected],
            is_published=True,
            is_practice=True,
        )
        created_quiz = self.quiz_repo.create_quiz(quiz_input)

        safe_questions = [
            QuestionStudentSafe(id=q.id, statement=q.statement, options=q.options)
            for q in created_quiz.questions
        ]
        return QuizStudentSafeResponse(
            id=created_quiz.id,
            course_id=created_quiz.course_id,
            title=created_quiz.title,
            description=created_quiz.description,
            topic_id=created_quiz.topic_id,
            questions=safe_questions,
        )

    # -------------------------------------------------------------------------
    # Quiz Submission, Automated Grading & Atomic Transaction (FR-13, FR-14, NFR-08)
    # -------------------------------------------------------------------------

    def submit_quiz_attempt(
        self,
        quiz_id: int,
        student_id: int,
        payload: QuizAttemptSubmitRequest,
    ) -> AttemptResultResponse:
        """Evaluate answers, calculate scores, and persist all records atomically (FR-13, NFR-08)."""
        quiz = self.quiz_repo.get_quiz_by_id(quiz_id)
        if quiz is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Quiz with ID {quiz_id} not found",
            )
        if not quiz.is_published:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot submit attempt for an unpublished quiz.",
            )
        self._require_student_enrollment(quiz.course_id, student_id)

        # Build lookup table of valid quiz questions
        quiz_question_map = {q.id: q for q in quiz.questions}
        if not quiz_question_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quiz contains zero questions.",
            )

        graded_answers: list[GradedAnswerResponse] = []
        earned_points: float = 0.0
        topic_stats: dict[int, dict[str, int]] = {}

        for item in payload.answers:
            if item.question_id not in quiz_question_map:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Question ID {item.question_id} does not belong to quiz {quiz_id}.",
                )
            q = quiz_question_map[item.question_id]

            if not (0 <= item.selected_option_index < len(q.options)):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Selected option index {item.selected_option_index} out of bounds for question {q.id}.",
                )

            is_correct = item.selected_option_index == q.correct_option_index
            if is_correct:
                earned_points += 1.0

            # Accumulate per-topic counters
            if q.topic_id not in topic_stats:
                topic_stats[q.topic_id] = {"correct": 0, "total": 0}
            topic_stats[q.topic_id]["total"] += 1
            if is_correct:
                topic_stats[q.topic_id]["correct"] += 1

            graded_answers.append(
                GradedAnswerResponse(
                    question_id=q.id,
                    statement=q.statement,
                    options=q.options,
                    selected_option_index=item.selected_option_index,
                    correct_option_index=q.correct_option_index,
                    is_correct=is_correct,
                    explanation=q.explanation,
                    topic_id=q.topic_id,
                    difficulty=q.difficulty,
                )
            )

        total_questions = len(quiz.questions)
        overall_score = round(earned_points / total_questions, 4) if total_questions > 0 else 0.0
        submitted_at_str = datetime.now(timezone.utc).isoformat()

        # Build topic breakdown
        topic_scores = [
            TopicScoreBreakdown(
                topic_id=tid,
                topic_score=round(counts["correct"] / counts["total"], 4) if counts["total"] > 0 else 0.0,
                correct_count=counts["correct"],
                total_questions=counts["total"],
            )
            for tid, counts in sorted(topic_stats.items())
        ]

        # ---------------------------------------------------------------------
        # EXECUTE SINGLE ATOMIC TRANSACTION (NFR-08)
        # ---------------------------------------------------------------------
        with self.session_factory() as session:
            try:
                # 1. Persist Attempt summary
                attempt_row = AttemptModel(
                    student_id=student_id,
                    course_id=quiz.course_id,
                    quiz_id=quiz.id,
                    quiz_title=quiz.title,
                    score=overall_score,
                    total_questions=total_questions,
                    submitted_at=submitted_at_str,
                )
                session.add(attempt_row)
                session.flush()
                assigned_attempt_id = attempt_row.attempt_id

                # 2. Persist Attempt Answers
                for ans in graded_answers:
                    ans_row = AttemptAnswerModel(
                        attempt_id=assigned_attempt_id,
                        question_id=ans.question_id,
                        selected_option_index=ans.selected_option_index,
                        is_correct=ans.is_correct,
                        topic_id=ans.topic_id,
                        difficulty_at_attempt=ans.difficulty,
                    )
                    session.add(ans_row)

                # 3. Update Course Question Stats (FR-24)
                for ans in graded_answers:
                    stat_row = (
                        session.query(QuestionStatsModel)
                        .filter_by(course_id=quiz.course_id, question_id=ans.question_id)
                        .first()
                    )
                    if not stat_row:
                        stat_row = QuestionStatsModel(
                            course_id=quiz.course_id,
                            question_id=ans.question_id,
                            question_text=ans.statement,
                            topic_id=ans.topic_id,
                            topic_name=f"Topic {ans.topic_id}",
                            difficulty=ans.difficulty,
                            times_answered=1,
                            correct_count=1 if ans.is_correct else 0,
                        )
                        session.add(stat_row)
                    else:
                        stat_row.times_answered += 1
                        if ans.is_correct:
                            stat_row.correct_count += 1

                # 4. Record Adaptive Engine Responses (FR-16)
                for ans in graded_answers:
                    resp_row = StudentTopicResponseModel(
                        student_id=student_id,
                        topic_id=ans.topic_id,
                        difficulty=ans.difficulty,
                        is_correct=ans.is_correct,
                    )
                    session.add(resp_row)

                session.commit()

            except Exception as exc:
                session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Atomic quiz submission transaction failed: {str(exc)}",
                ) from exc

        return AttemptResultResponse(
            attempt_id=assigned_attempt_id,
            quiz_id=quiz.id,
            quiz_title=quiz.title,
            score=overall_score,
            total_questions=total_questions,
            correct_answers=int(earned_points),
            submitted_at=submitted_at_str,
            topic_scores=topic_scores,
            answers=graded_answers,
        )

    def get_attempt_result(
        self,
        attempt_id: int,
        user_id: int,
        role: str,
    ) -> AttemptResultResponse:
        """Retrieve attempt results with privacy checks (FR-14, NFR-06)."""
        with self.session_factory() as session:
            attempt = session.query(AttemptModel).filter_by(attempt_id=attempt_id).first()
            if attempt is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Attempt with ID {attempt_id} not found",
                )

            # Privacy checks
            is_student_owner = (role.lower() == "student" and attempt.student_id == user_id)
            is_instructor_owner = (
                role.lower() == "instructor"
                and self.progress_repo.is_course_owner(attempt.course_id, user_id)
            )

            if not (is_student_owner or is_instructor_owner):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: you cannot view attempt results belonging to other students.",
                )

            # Query detailed answers
            answer_rows = (
                session.query(AttemptAnswerModel)
                .filter_by(attempt_id=attempt_id)
                .order_by(AttemptAnswerModel.id.asc())
                .all()
            )

            graded_answers: list[GradedAnswerResponse] = []
            topic_stats: dict[int, dict[str, int]] = {}

            for ar in answer_rows:
                q = session.query(QuestionModel).filter_by(id=ar.question_id).first()
                stmt = q.statement if q else "Question"
                opts = q.options if q else []
                correct_idx = q.correct_option_index if q else 0
                exp = q.explanation if q else None

                if ar.topic_id not in topic_stats:
                    topic_stats[ar.topic_id] = {"correct": 0, "total": 0}
                topic_stats[ar.topic_id]["total"] += 1
                if ar.is_correct:
                    topic_stats[ar.topic_id]["correct"] += 1

                graded_answers.append(
                    GradedAnswerResponse(
                        question_id=ar.question_id,
                        statement=stmt,
                        options=opts,
                        selected_option_index=ar.selected_option_index,
                        correct_option_index=correct_idx,
                        is_correct=ar.is_correct,
                        explanation=exp,
                        topic_id=ar.topic_id,
                        difficulty=ar.difficulty_at_attempt,
                    )
                )

            topic_scores = [
                TopicScoreBreakdown(
                    topic_id=tid,
                    topic_score=round(counts["correct"] / counts["total"], 4) if counts["total"] > 0 else 0.0,
                    correct_count=counts["correct"],
                    total_questions=counts["total"],
                )
                for tid, counts in sorted(topic_stats.items())
            ]

            return AttemptResultResponse(
                attempt_id=attempt.attempt_id,
                quiz_id=attempt.quiz_id,
                quiz_title=attempt.quiz_title,
                score=attempt.score,
                total_questions=attempt.total_questions,
                correct_answers=sum(1 for a in graded_answers if a.is_correct),
                submitted_at=attempt.submitted_at,
                topic_scores=topic_scores,
                answers=graded_answers,
            )

    # -------------------------------------------------------------------------
    # Helper & Authorization Guards
    # -------------------------------------------------------------------------

    def _require_course_owner(self, course_id: int, instructor_id: int) -> None:
        """Assert instructor is owner of course, otherwise raise HTTP 403."""
        if not self.progress_repo.is_course_owner(course_id, instructor_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: instructor {instructor_id} is not the owner of course {course_id}",
            )

    def _require_student_enrollment(self, course_id: int, student_id: int) -> None:
        """Assert student is enrolled in course, otherwise raise HTTP 403."""
        if not self.progress_repo.is_student_enrolled(student_id, course_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: student {student_id} is not enrolled in course {course_id}",
            )

    @staticmethod
    def _to_question_response(q: QuestionRecord) -> QuestionResponse:
        return QuestionResponse(
            id=q.id,
            course_id=q.course_id,
            topic_id=q.topic_id,
            statement=q.statement,
            options=q.options,
            correct_option_index=q.correct_option_index,
            difficulty=q.difficulty,
            explanation=q.explanation,
            is_active=q.is_active,
            created_at=q.created_at,
        )

    @staticmethod
    def _to_quiz_response(q: QuizRecord) -> QuizResponse:
        return QuizResponse(
            id=q.id,
            course_id=q.course_id,
            title=q.title,
            description=q.description,
            topic_id=q.topic_id,
            is_published=q.is_published,
            is_practice=q.is_practice,
            questions=[QuizService._to_question_response(item) for item in q.questions],
            created_at=q.created_at,
        )


# Global singleton instance for dependency injection
_global_quiz_service: Optional[QuizService] = None


def get_quiz_service() -> QuizService:
    """FastAPI dependency provider for QuizService."""
    global _global_quiz_service
    if _global_quiz_service is None:
        _global_quiz_service = QuizService()
    return _global_quiz_service
