"""Pydantic v2 validation schemas for Module 2: Quiz & Assessment Engine.

Requirements Traceability:
- FR-08: Question creation & bounds validation (2-5 options, correct index 0..len-1, difficulty).
- FR-10: Quiz configuration and authoring schemas.
- FR-11: Student-safe question presentation (strict omission of correct options and explanations).
- FR-12: Practice quiz request schemas with bounding limits.
- FR-13: Quiz attempt submission schemas with answer arrays.
- FR-14: Graded attempt results and topic breakdown schemas.
- FR-25: Descriptive user input error messages without stack trace leakage.
- Decision D3: Storing options as JSON array with integer correct index.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

VALID_DIFFICULTIES: frozenset[str] = frozenset({"Easy", "Medium", "Hard"})


# =============================================================================
# Question Schemas (FR-08, FR-09, FR-11)
# =============================================================================


class QuestionCreate(BaseModel):
    """Payload for creating a multiple-choice question in a course topic (FR-08, Decision D3)."""

    statement: str = Field(..., description="The non-empty question statement text")
    options: list[str] = Field(..., description="Array of 2 to 5 distinct option strings")
    correct_option_index: int = Field(..., ge=0, description="Zero-based index of correct option")
    difficulty: str = Field(..., description="Difficulty level ('Easy', 'Medium', 'Hard')")
    topic_id: int | None = Field(default=None, description="Optional associated topic ID")
    explanation: str | None = Field(
        default=None, description="Pedagogical explanation for feedback"
    )

    @field_validator("statement")
    @classmethod
    def validate_statement(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Statement cannot be empty or whitespace only")
        return stripped

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[str]) -> list[str]:
        if not (2 <= len(v) <= 5):
            raise ValueError(f"Options list must contain between 2 and 5 choices, got {len(v)}")
        cleaned = []
        for idx, opt in enumerate(v):
            stripped = opt.strip()
            if not stripped:
                raise ValueError(
                    f"Option choices cannot be empty or whitespace only (found at index {idx})"
                )
            cleaned.append(stripped)
        return cleaned

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        normalized = v.strip().capitalize()
        if normalized not in VALID_DIFFICULTIES:
            raise ValueError(f"Difficulty must be one of {sorted(VALID_DIFFICULTIES)}, got '{v}'")
        return normalized

    @model_validator(mode="after")
    def validate_correct_index_within_options(self) -> "QuestionCreate":
        if self.options and not (0 <= self.correct_option_index < len(self.options)):
            raise ValueError(
                f"correct_option_index ({self.correct_option_index}) out of bounds "
                f"for options of length {len(self.options)} (must be 0 to {len(self.options) - 1})"
            )
        return self

    model_config = ConfigDict(str_strip_whitespace=True)


class QuestionUpdate(BaseModel):
    """Payload for updating an existing question (FR-08)."""

    statement: str | None = Field(default=None, min_length=1)
    options: list[str] | None = None
    correct_option_index: int | None = Field(default=None, ge=0)
    difficulty: str | None = None
    explanation: str | None = None
    is_active: bool | None = None

    @field_validator("statement")
    @classmethod
    def validate_statement(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Statement cannot be empty or whitespace only")
        return v.strip() if v else v

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            if not (2 <= len(v) <= 5):
                raise ValueError(f"Options list must contain between 2 and 5 choices, got {len(v)}")
            cleaned = []
            for idx, opt in enumerate(v):
                stripped = opt.strip()
                if not stripped:
                    raise ValueError(f"Option choices cannot be empty (index {idx})")
                cleaned.append(stripped)
            return cleaned
        return v

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str | None) -> str | None:
        if v is not None:
            normalized = v.strip().capitalize()
            if normalized not in VALID_DIFFICULTIES:
                raise ValueError(
                    f"Difficulty must be one of {sorted(VALID_DIFFICULTIES)}, got '{v}'"
                )
            return normalized
        return v

    @model_validator(mode="after")
    def validate_index_against_options(self) -> "QuestionUpdate":
        if (
            self.options is not None
            and self.correct_option_index is not None
            and not (0 <= self.correct_option_index < len(self.options))
        ):
            raise ValueError(
                f"correct_option_index ({self.correct_option_index}) out of bounds "
                f"for options of length {len(self.options)}"
            )
        return self


class QuestionResponse(BaseModel):
    """Full question details for instructors (including correct answer and explanation)."""

    id: int
    course_id: int
    topic_id: int
    statement: str
    options: list[str]
    correct_option_index: int
    difficulty: str
    explanation: str | None = None
    is_active: bool = True
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class QuestionStudentSafe(BaseModel):
    """Student-safe question representation (FR-11: strictly strips correct answers and explanations)."""

    id: int
    statement: str
    options: list[str]

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Quiz Schemas (FR-10, FR-11, FR-12)
# =============================================================================


class QuizCreate(BaseModel):
    """Payload for instructor creating a quiz (FR-10)."""

    title: str = Field(..., min_length=1, max_length=200, description="Quiz title")
    description: str | None = Field(default=None, description="Optional quiz instructions")
    topic_id: int | None = Field(default=None, description="Optional single topic association")
    question_ids: list[int] = Field(default_factory=list, description="Ordered question IDs")
    is_published: bool = Field(default=False, description="Whether quiz is active for students")
    is_practice: bool = Field(
        default=False, description="Whether quiz is an on-demand practice quiz"
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Title cannot be empty or whitespace only")
        return stripped


class QuizUpdate(BaseModel):
    """Payload for updating quiz metadata (FR-10)."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    is_published: bool | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip() if v else v


class QuizAddQuestionsRequest(BaseModel):
    """Payload to append question IDs to a quiz."""

    question_ids: list[int] = Field(..., min_length=1, description="Question IDs to add")


class QuizSummaryResponse(BaseModel):
    """Brief summary of a quiz for course listings."""

    id: int
    course_id: int
    title: str
    description: str | None = None
    topic_id: int | None = None
    is_published: bool
    is_practice: bool
    question_count: int = 0
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class QuizResponse(BaseModel):
    """Full quiz detail for course instructors including all question answers."""

    id: int
    course_id: int
    title: str
    description: str | None = None
    topic_id: int | None = None
    is_published: bool
    is_practice: bool
    questions: list[QuestionResponse] = Field(default_factory=list)
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class QuizStudentSafeResponse(BaseModel):
    """Student-safe quiz view for taking assessments (FR-11)."""

    id: int
    course_id: int
    title: str
    description: str | None = None
    topic_id: int | None = None
    questions: list[QuestionStudentSafe] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PracticeQuizRequest(BaseModel):
    """Payload to generate an on-demand dynamic topic practice quiz (FR-12)."""

    topic_id: int = Field(..., description="Topic for which to assemble practice questions")
    question_count: int = Field(default=5, ge=1, le=20, description="Desired question count (1-20)")


# =============================================================================
# Attempt Submission & Grading Schemas (FR-13, FR-14)
# =============================================================================


class AnswerSubmissionItem(BaseModel):
    """Individual question answer in an attempt submission (FR-13)."""

    question_id: int = Field(..., description="Target question ID")
    selected_option_index: int = Field(..., ge=0, description="Selected option index (0-based)")


class QuizAttemptSubmitRequest(BaseModel):
    """Payload submitted by student to grade and complete a quiz attempt (FR-13)."""

    answers: list[AnswerSubmissionItem] = Field(..., description="List of submitted answers")
    idempotency_key: str | None = Field(
        default=None, description="Optional key to prevent double submits"
    )

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, v: list[AnswerSubmissionItem]) -> list[AnswerSubmissionItem]:
        if not v:
            raise ValueError("Answers list cannot be empty")
        return v


class TopicScoreBreakdown(BaseModel):
    """Topic-level performance summary in a graded attempt (FR-14)."""

    topic_id: int
    topic_score: float = Field(
        ..., ge=0.0, le=1.0, description="Proportion correct in topic (0.0 to 1.0)"
    )
    correct_count: int = Field(..., ge=0)
    total_questions: int = Field(..., ge=0)


class GradedAnswerResponse(BaseModel):
    """Individual question result returned after submission (FR-14)."""

    question_id: int
    statement: str
    options: list[str]
    selected_option_index: int
    correct_option_index: int
    is_correct: bool
    explanation: str | None = None
    topic_id: int
    difficulty: str


class AttemptResultResponse(BaseModel):
    """Comprehensive graded attempt result displayed to student and instructor (FR-14)."""

    attempt_id: int
    quiz_id: int
    quiz_title: str
    score: float = Field(..., ge=0.0, le=1.0, description="Overall proportion score (0.0 to 1.0)")
    total_questions: int = Field(..., ge=0)
    correct_answers: int = Field(..., ge=0)
    submitted_at: str
    topic_scores: list[TopicScoreBreakdown] = Field(default_factory=list)
    answers: list[GradedAnswerResponse] = Field(default_factory=list)
