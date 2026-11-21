"""Repository layer for Quiz and Question data access (AdaptLearn M2).

Requirements Traceability:
- FR-08: Question CRUD, difficulty, options, topic and course association.
- FR-09: Soft-delete answered questions (is_active = False if attempt answers exist).
- FR-10: Quiz creation, question ordering, publishing toggle.
- FR-11: Quiz retrieval and question bank access.
- FR-12: Topic practice quiz question queries.
- FR-13: Question-level attempt answer persistence.
- NFR-07: Parameterized queries / ORM mapping.
- NFR-08: Persistent database transactions and restart survival.
- NFR-09: Referential integrity and relational constraints.
"""
from dataclasses import dataclass, field
from datetime import datetime
import json
from typing import Optional, Sequence

from sqlalchemy.orm import Session, sessionmaker

from app.db.session import SessionLocal, init_db
from app.models.quiz import AttemptAnswerModel, QuestionModel, QuizModel, QuizQuestionModel


@dataclass
class QuestionRecordInput:
    """Input DTO for creating or updating a question entity."""
    course_id: int
    topic_id: int
    statement: str
    options: list[str]
    correct_option_index: int
    difficulty: str  # 'Easy', 'Medium', 'Hard'
    explanation: Optional[str] = None
    is_active: bool = True


@dataclass(frozen=True)
class QuestionRecord:
    """Read-only domain representation of a persisted question."""
    id: int
    course_id: int
    topic_id: int
    statement: str
    options: list[str]
    correct_option_index: int
    difficulty: str
    explanation: Optional[str]
    is_active: bool
    created_at: Optional[datetime] = None


@dataclass
class QuizRecordInput:
    """Input DTO for creating a quiz."""
    course_id: int
    title: str
    question_ids: Sequence[int] = ()
    description: Optional[str] = None
    topic_id: Optional[int] = None
    is_published: bool = False
    is_practice: bool = False


@dataclass(frozen=True)
class QuizRecord:
    """Read-only domain representation of a persisted quiz."""
    id: int
    course_id: int
    title: str
    description: Optional[str]
    topic_id: Optional[int]
    is_published: bool
    is_practice: bool
    questions: list[QuestionRecord] = field(default_factory=list)
    created_at: Optional[datetime] = None


@dataclass
class AnswerRecordInput:
    """Input DTO for recording an answer in a quiz attempt."""
    attempt_id: int
    question_id: int
    selected_option_index: int
    is_correct: bool
    topic_id: int
    difficulty_at_attempt: str


@dataclass(frozen=True)
class AnswerRecord:
    """Read-only domain representation of an attempt answer."""
    id: int
    attempt_id: int
    question_id: int
    selected_option_index: int
    is_correct: bool
    topic_id: int
    difficulty_at_attempt: str


def _to_question_record(row: QuestionModel) -> QuestionRecord:
    """Map QuestionModel ORM row to QuestionRecord dataclass."""
    try:
        opts = json.loads(row.options_json) if row.options_json else []
    except Exception:
        opts = []
    return QuestionRecord(
        id=row.id,
        course_id=row.course_id,
        topic_id=row.topic_id,
        statement=row.statement,
        options=opts,
        correct_option_index=row.correct_option_index,
        difficulty=row.difficulty,
        explanation=row.explanation,
        is_active=row.is_active,
        created_at=row.created_at,
    )


class QuizRepository:
    """SQLAlchemy persistent repository for quizzes, questions, and attempt answers."""

    def __init__(self, session_factory: Optional[sessionmaker[Session]] = None) -> None:
        self.session_factory = session_factory or SessionLocal
        init_db()

    def clear(self) -> None:
        """Reset repository tables (used for test isolation)."""
        with self.session_factory() as session:
            session.query(AttemptAnswerModel).delete()
            session.query(QuizQuestionModel).delete()
            session.query(QuizModel).delete()
            session.query(QuestionModel).delete()
            session.commit()

    # -------------------------------------------------------------------------
    # Question Management (FR-08, FR-09, FR-12)
    # -------------------------------------------------------------------------

    def create_question(self, question_input: QuestionRecordInput) -> QuestionRecord:
        """Create and persist a new question entity (FR-08)."""
        with self.session_factory() as session:
            row = QuestionModel(
                course_id=question_input.course_id,
                topic_id=question_input.topic_id,
                statement=question_input.statement,
                options_json=json.dumps(question_input.options),
                correct_option_index=question_input.correct_option_index,
                difficulty=question_input.difficulty,
                explanation=question_input.explanation,
                is_active=question_input.is_active,
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return _to_question_record(row)

    def get_question_by_id(self, question_id: int) -> Optional[QuestionRecord]:
        """Retrieve question by primary key."""
        with self.session_factory() as session:
            row = session.query(QuestionModel).filter_by(id=question_id).first()
            if row is None:
                return None
            return _to_question_record(row)

    def update_question(
        self,
        question_id: int,
        statement: Optional[str] = None,
        options: Optional[list[str]] = None,
        correct_option_index: Optional[int] = None,
        difficulty: Optional[str] = None,
        explanation: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[QuestionRecord]:
        """Update question attributes (FR-08)."""
        with self.session_factory() as session:
            row = session.query(QuestionModel).filter_by(id=question_id).first()
            if row is None:
                return None

            if statement is not None:
                row.statement = statement
            if options is not None:
                row.options_json = json.dumps(options)
            if correct_option_index is not None:
                row.correct_option_index = correct_option_index
            if difficulty is not None:
                row.difficulty = difficulty
            if explanation is not None:
                row.explanation = explanation
            if is_active is not None:
                row.is_active = is_active

            session.commit()
            session.refresh(row)
            return _to_question_record(row)

    def delete_question(self, question_id: int) -> bool:
        """Delete or soft-delete question (FR-09).

        Returns:
            bool: True if soft-deleted (is_active=False due to existing attempt answers);
                  False if hard-deleted (removed entirely from database).
        """
        with self.session_factory() as session:
            row = session.query(QuestionModel).filter_by(id=question_id).first()
            if row is None:
                return False

            has_answers = (
                session.query(AttemptAnswerModel.id).filter_by(question_id=question_id).first()
                is not None
            )

            if has_answers:
                row.is_active = False
                session.commit()
                return True

            # If no answers exist, hard delete question and associations
            session.query(QuizQuestionModel).filter_by(question_id=question_id).delete()
            session.delete(row)
            session.commit()
            return False

    def get_active_questions_by_topic(self, course_id: int, topic_id: int) -> list[QuestionRecord]:
        """Retrieve active questions for a topic, for practice quiz generation (FR-12)."""
        with self.session_factory() as session:
            rows = (
                session.query(QuestionModel)
                .filter_by(course_id=course_id, topic_id=topic_id, is_active=True)
                .order_by(QuestionModel.id.asc())
                .all()
            )
            return [_to_question_record(r) for r in rows]

    def get_course_questions(
        self, course_id: int, topic_id: Optional[int] = None, active_only: bool = True
    ) -> list[QuestionRecord]:
        """Retrieve all questions for a course with optional topic and active status filters."""
        with self.session_factory() as session:
            q = session.query(QuestionModel).filter_by(course_id=course_id)
            if topic_id is not None:
                q = q.filter_by(topic_id=topic_id)
            if active_only:
                q = q.filter_by(is_active=True)
            rows = q.order_by(QuestionModel.id.asc()).all()
            return [_to_question_record(r) for r in rows]

    # -------------------------------------------------------------------------
    # Quiz Management (FR-10, FR-11)
    # -------------------------------------------------------------------------

    def create_quiz(self, quiz_input: QuizRecordInput) -> QuizRecord:
        """Create a quiz and associate questions with ordered sequence (FR-10)."""
        with self.session_factory() as session:
            quiz_row = QuizModel(
                course_id=quiz_input.course_id,
                title=quiz_input.title,
                description=quiz_input.description,
                topic_id=quiz_input.topic_id,
                is_published=quiz_input.is_published,
                is_practice=quiz_input.is_practice,
            )
            session.add(quiz_row)
            session.flush()

            for idx, qid in enumerate(quiz_input.question_ids):
                link = QuizQuestionModel(
                    quiz_id=quiz_row.id,
                    question_id=qid,
                    order_index=idx,
                )
                session.add(link)

            session.commit()
            session.refresh(quiz_row)
            return self._load_quiz_with_questions(session, quiz_row)

    def _load_quiz_with_questions(self, session: Session, quiz_row: QuizModel) -> QuizRecord:
        """Helper to assemble QuizRecord with ordered questions list."""
        links = (
            session.query(QuizQuestionModel)
            .filter_by(quiz_id=quiz_row.id)
            .order_by(QuizQuestionModel.order_index.asc())
            .all()
        )
        questions: list[QuestionRecord] = []
        for link in links:
            q_row = session.query(QuestionModel).filter_by(id=link.question_id).first()
            if q_row:
                questions.append(_to_question_record(q_row))

        return QuizRecord(
            id=quiz_row.id,
            course_id=quiz_row.course_id,
            title=quiz_row.title,
            description=quiz_row.description,
            topic_id=quiz_row.topic_id,
            is_published=quiz_row.is_published,
            is_practice=quiz_row.is_practice,
            questions=questions,
            created_at=quiz_row.created_at,
        )

    def get_quiz_by_id(self, quiz_id: int) -> Optional[QuizRecord]:
        """Retrieve quiz and all associated questions in presentation order (FR-11)."""
        with self.session_factory() as session:
            row = session.query(QuizModel).filter_by(id=quiz_id).first()
            if row is None:
                return None
            return self._load_quiz_with_questions(session, row)

    def set_quiz_published(self, quiz_id: int, is_published: bool) -> Optional[QuizRecord]:
        """Toggle quiz publication visibility (FR-10)."""
        with self.session_factory() as session:
            row = session.query(QuizModel).filter_by(id=quiz_id).first()
            if row is None:
                return None
            row.is_published = is_published
            session.commit()
            session.refresh(row)
            return self._load_quiz_with_questions(session, row)

    def get_course_quizzes(self, course_id: int, published_only: bool = False) -> list[QuizRecord]:
        """Retrieve all quizzes for a course, optionally filtering by published status."""
        with self.session_factory() as session:
            q = session.query(QuizModel).filter_by(course_id=course_id)
            if published_only:
                q = q.filter_by(is_published=True)
            rows = q.order_by(QuizModel.id.asc()).all()
            return [self._load_quiz_with_questions(session, r) for r in rows]

    # -------------------------------------------------------------------------
    # Attempt Answers (FR-13, FR-14)
    # -------------------------------------------------------------------------

    def record_attempt_answers(
        self,
        answers: list[AnswerRecordInput],
        session: Optional[Session] = None,
    ) -> list[AnswerRecord]:
        """Persist detailed answers submitted in an attempt (participates in external session)."""
        def _execute(s: Session) -> list[AnswerRecord]:
            created_records: list[AnswerRecord] = []
            for item in answers:
                row = AttemptAnswerModel(
                    attempt_id=item.attempt_id,
                    question_id=item.question_id,
                    selected_option_index=item.selected_option_index,
                    is_correct=item.is_correct,
                    topic_id=item.topic_id,
                    difficulty_at_attempt=item.difficulty_at_attempt,
                )
                s.add(row)
                s.flush()
                created_records.append(
                    AnswerRecord(
                        id=row.id,
                        attempt_id=row.attempt_id,
                        question_id=row.question_id,
                        selected_option_index=row.selected_option_index,
                        is_correct=row.is_correct,
                        topic_id=row.topic_id,
                        difficulty_at_attempt=row.difficulty_at_attempt,
                    )
                )
            return created_records

        if session is not None:
            return _execute(session)
        else:
            with self.session_factory() as new_session:
                res = _execute(new_session)
                new_session.commit()
                return res

    def get_attempt_answers(self, attempt_id: int) -> list[AnswerRecord]:
        """Retrieve all answers associated with a specific quiz attempt (FR-14)."""
        with self.session_factory() as session:
            rows = (
                session.query(AttemptAnswerModel)
                .filter_by(attempt_id=attempt_id)
                .order_by(AttemptAnswerModel.id.asc())
                .all()
            )
            return [
                AnswerRecord(
                    id=r.id,
                    attempt_id=r.attempt_id,
                    question_id=r.question_id,
                    selected_option_index=r.selected_option_index,
                    is_correct=r.is_correct,
                    topic_id=r.topic_id,
                    difficulty_at_attempt=r.difficulty_at_attempt,
                )
                for r in rows
            ]


# Global singleton instance for dependency injection
_global_quiz_repo: Optional[QuizRepository] = None


def get_quiz_repository() -> QuizRepository:
    """FastAPI dependency provider for QuizRepository."""
    global _global_quiz_repo
    if _global_quiz_repo is None:
        _global_quiz_repo = QuizRepository()
    return _global_quiz_repo
