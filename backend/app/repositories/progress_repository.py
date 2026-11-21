"""Repository for student progress, attempt history, and instructor analytics data (AdaptLearn M5).

Requirements Traceability:
- FR-15: Attempt history storage and retrieval with pagination.
- FR-21: Enrollment verification and recent attempts querying for dashboard.
- FR-22: Enrolled student roster lookups.
- FR-23: Course enrolled student aggregation for mastery distributions.
- FR-24: Question statistics tracking (times answered, correct count).
- NFR-05 & NFR-06: Server-side enrollment and ownership lookups for access control.
- NFR-07 & NFR-08: Persistent database transactions and ACID durability.
"""
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session, sessionmaker

from app.db.session import SessionLocal, init_db
from app.models.progress import AttemptModel, CourseOwnerModel, EnrollmentModel, QuestionStatsModel


@dataclass(frozen=True)
class AttemptRecord:
    """Historical representation of a completed quiz attempt."""
    attempt_id: int
    student_id: int
    course_id: int
    quiz_id: int
    quiz_title: str
    score: float
    total_questions: int
    submitted_at: str


@dataclass
class QuestionStatsRecord:
    """Aggregated statistics for a specific course question (FR-24)."""
    question_id: int
    question_text: str
    topic_id: int
    topic_name: str
    difficulty: str
    times_answered: int = 0
    correct_count: int = 0


class ProgressRepository:
    """SQLAlchemy persistent repository for progress, attempts, and question analytics.

    Provides durable relational storage surviving application restart.
    """

    def __init__(self, session_factory: Optional[sessionmaker[Session]] = None) -> None:
        self.session_factory = session_factory or SessionLocal
        init_db()

    def clear(self) -> None:
        """Reset repository state (for test isolation)."""
        with self.session_factory() as session:
            session.query(QuestionStatsModel).delete()
            session.query(AttemptModel).delete()
            session.query(CourseOwnerModel).delete()
            session.query(EnrollmentModel).delete()
            session.commit()

    def enroll_student(self, student_id: int, course_id: int) -> None:
        """Record a student's enrollment in a course."""
        with self.session_factory() as session:
            existing = session.query(EnrollmentModel).filter_by(student_id=student_id, course_id=course_id).first()
            if not existing:
                row = EnrollmentModel(student_id=student_id, course_id=course_id)
                session.add(row)
                session.commit()

    def is_student_enrolled(self, student_id: int, course_id: int) -> bool:
        """Verify if a student is enrolled in a specific course."""
        with self.session_factory() as session:
            return session.query(EnrollmentModel).filter_by(student_id=student_id, course_id=course_id).first() is not None

    def get_course_enrolled_students(self, course_id: int) -> list[int]:
        """Retrieve sorted list of student IDs enrolled in a course."""
        with self.session_factory() as session:
            rows = session.query(EnrollmentModel.student_id).filter_by(course_id=course_id).all()
            return sorted([r[0] for r in rows])

    def set_course_owner(self, course_id: int, instructor_id: int) -> None:
        """Associate an instructor as the owner of a course."""
        with self.session_factory() as session:
            row = session.query(CourseOwnerModel).filter_by(course_id=course_id).first()
            if not row:
                row = CourseOwnerModel(course_id=course_id, instructor_id=instructor_id)
                session.add(row)
            else:
                row.instructor_id = instructor_id
            session.commit()

    def is_course_owner(self, course_id: int, instructor_id: int) -> bool:
        """Check if an instructor is the owner of a course."""
        with self.session_factory() as session:
            row = session.query(CourseOwnerModel).filter_by(course_id=course_id).first()
            return row.instructor_id == instructor_id if row else False

    def record_attempt(self, attempt: AttemptRecord) -> None:
        """Store a completed attempt record."""
        with self.session_factory() as session:
            row = AttemptModel(
                attempt_id=attempt.attempt_id,
                student_id=attempt.student_id,
                course_id=attempt.course_id,
                quiz_id=attempt.quiz_id,
                quiz_title=attempt.quiz_title,
                score=attempt.score,
                total_questions=attempt.total_questions,
                submitted_at=attempt.submitted_at,
            )
            session.merge(row)
            session.commit()

    def get_student_attempts(
        self, student_id: int, course_id: int, limit: int = 10, offset: int = 0
    ) -> tuple[list[AttemptRecord], int]:
        """Retrieve paginated student attempts in reverse chronological order (newest first)."""
        with self.session_factory() as session:
            q = session.query(AttemptModel).filter_by(student_id=student_id, course_id=course_id)
            total_count = q.count()
            rows = q.order_by(AttemptModel.attempt_id.desc()).offset(offset).limit(limit).all()
            attempts = [
                AttemptRecord(
                    attempt_id=r.attempt_id,
                    student_id=r.student_id,
                    course_id=r.course_id,
                    quiz_id=r.quiz_id,
                    quiz_title=r.quiz_title,
                    score=r.score,
                    total_questions=r.total_questions,
                    submitted_at=r.submitted_at,
                )
                for r in rows
            ]
            return attempts, total_count

    def add_course_question(
        self,
        course_id: int,
        question_id: int,
        question_text: str,
        topic_id: int,
        topic_name: str,
        difficulty: str,
    ) -> None:
        """Register a question in a course for analytics tracking (FR-24)."""
        with self.session_factory() as session:
            row = session.query(QuestionStatsModel).filter_by(course_id=course_id, question_id=question_id).first()
            if not row:
                row = QuestionStatsModel(
                    course_id=course_id,
                    question_id=question_id,
                    question_text=question_text,
                    topic_id=topic_id,
                    topic_name=topic_name,
                    difficulty=difficulty,
                    times_answered=0,
                    correct_count=0,
                )
                session.add(row)
            else:
                row.question_text = question_text
                row.topic_id = topic_id
                row.topic_name = topic_name
                row.difficulty = difficulty
            session.commit()

    def record_question_response(
        self,
        course_id: int,
        question_id: int,
        question_text: str,
        topic_id: int,
        topic_name: str,
        difficulty: str,
        is_correct: bool,
        count: int = 1,
    ) -> None:
        """Increment answer metrics for a question (FR-24)."""
        with self.session_factory() as session:
            row = session.query(QuestionStatsModel).filter_by(course_id=course_id, question_id=question_id).first()
            if not row:
                row = QuestionStatsModel(
                    course_id=course_id,
                    question_id=question_id,
                    question_text=question_text,
                    topic_id=topic_id,
                    topic_name=topic_name,
                    difficulty=difficulty,
                    times_answered=count,
                    correct_count=count if is_correct else 0,
                )
                session.add(row)
            else:
                row.times_answered += count
                if is_correct:
                    row.correct_count += count
            session.commit()

    def get_course_question_stats(self, course_id: int) -> list[QuestionStatsRecord]:
        """Retrieve question answering statistics for a course in deterministic order."""
        with self.session_factory() as session:
            rows = (
                session.query(QuestionStatsModel)
                .filter_by(course_id=course_id)
                .order_by(QuestionStatsModel.question_id.asc())
                .all()
            )
            return [
                QuestionStatsRecord(
                    question_id=r.question_id,
                    question_text=r.question_text,
                    topic_id=r.topic_id,
                    topic_name=r.topic_name,
                    difficulty=r.difficulty,
                    times_answered=r.times_answered,
                    correct_count=r.correct_count,
                )
                for r in rows
            ]


# Global singleton instance for dependency injection
_global_progress_repo: ProgressRepository | None = None


def get_progress_repository() -> ProgressRepository:
    """FastAPI dependency provider for ProgressRepository."""
    global _global_progress_repo
    if _global_progress_repo is None:
        _global_progress_repo = ProgressRepository()
    return _global_progress_repo
