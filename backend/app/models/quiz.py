"""SQLAlchemy ORM models for Module 2: Quiz & Assessment Engine.

Requirements Traceability:
- FR-08: Multiple-choice question bank entities and attributes.
- FR-09: Soft-delete capability for answered questions (is_active flag).
- FR-10: Quiz entities, topic associations, and publication status.
- FR-11: Quiz-question presentation sequence association.
- FR-12: Topic practice quiz support.
- FR-13: Question-level student attempt answer records.
- NFR-07 & NFR-09: Relational schema constraints and foreign keys.
- Decision D2 & D3: JSON array options, single correct option index, join table.
"""
from datetime import datetime, timezone
import json

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


def utc_now() -> datetime:
    """Return current UTC timestamp with timezone awareness."""
    return datetime.now(timezone.utc)


class QuestionModel(Base):
    """Multiple-choice assessment question entity (FR-08, FR-09)."""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    course_id = Column(Integer, nullable=False, index=True)
    topic_id = Column(Integer, nullable=False, index=True)
    statement = Column(Text, nullable=False)
    options_json = Column(Text, nullable=False)  # JSON array of 2-5 strings
    correct_option_index = Column(Integer, nullable=False)  # 0-based index
    difficulty = Column(String(20), nullable=False)  # 'Easy', 'Medium', 'Hard'
    explanation = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    @property
    def options(self) -> list[str]:
        """Deserialize JSON options into a list of strings."""
        try:
            return json.loads(self.options_json) if self.options_json else []
        except Exception:
            return []

    @options.setter
    def options(self, val: list[str]) -> None:
        """Serialize a list of strings into JSON."""
        self.options_json = json.dumps(val)


class QuizModel(Base):
    """Formal assessment or practice quiz entity (FR-10, FR-12)."""
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    course_id = Column(Integer, nullable=False, index=True)
    topic_id = Column(Integer, nullable=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    is_published = Column(Boolean, nullable=False, default=False, index=True)
    is_practice = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class QuizQuestionModel(Base):
    """Join table associating questions with quizzes in presentation sequence (FR-10, FR-11)."""
    __tablename__ = "quiz_questions"

    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), primary_key=True)
    order_index = Column(Integer, nullable=False, default=0)


class AttemptAnswerModel(Base):
    """Individual question answer submitted during a quiz attempt (FR-13, FR-14)."""
    __tablename__ = "attempt_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    attempt_id = Column(Integer, nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    selected_option_index = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    topic_id = Column(Integer, nullable=False, index=True)
    difficulty_at_attempt = Column(String(20), nullable=False)
