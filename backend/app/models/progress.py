"""SQLAlchemy ORM models for Module 5: Progress Analytics & Instructor Dashboard."""

from sqlalchemy import Column, Float, Integer, String, Text, UniqueConstraint

from app.db.base import Base
from app.models.course import EnrollmentModel

__all__ = [
    "AttemptModel",
    "CourseOwnerModel",
    "EnrollmentModel",
    "QuestionStatsModel",
]


class CourseOwnerModel(Base):
    """Course ownership mapping for instructors (NFR-05, NFR-06)."""

    __tablename__ = "course_owners"

    course_id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, nullable=False, index=True)


class AttemptModel(Base):
    """Completed student quiz attempt records (FR-15, FR-21)."""

    __tablename__ = "quiz_attempts"

    attempt_id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, nullable=False, index=True)
    course_id = Column(Integer, nullable=False, index=True)
    quiz_id = Column(Integer, nullable=False, index=True)
    quiz_title = Column(String(200), nullable=False)
    score = Column(Float, nullable=False)
    total_questions = Column(Integer, nullable=False)
    submitted_at = Column(String(50), nullable=False)


class QuestionStatsModel(Base):
    """Aggregated question metrics for instructor analytics (FR-24)."""

    __tablename__ = "course_question_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, nullable=False, index=True)
    question_id = Column(Integer, nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    topic_id = Column(Integer, nullable=False)
    topic_name = Column(String(100), nullable=False)
    difficulty = Column(String(20), nullable=False)
    times_answered = Column(Integer, nullable=False, default=0)
    correct_count = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("course_id", "question_id", name="uq_course_question_stats"),
    )
