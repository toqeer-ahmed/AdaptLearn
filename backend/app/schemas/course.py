"""Pydantic schemas for Module 1: User & Course Management.

Requirements Traceability:
- FR-04: Course creation, unique course codes, instructor ownership.
- FR-05: Course lifecycle, editing, and archiving.
- FR-06: Topic creation, sequential order indexing.
- FR-07: Sequential topic reordering.
- FR-08: Topic prerequisite relationships and dependencies.
- FR-09: Prerequisite graph integrity.
- FR-10: Student course enrollment.
- Decisions: D1 (course code uppercase/alphanumeric), D2 (topic validation), D3 (archiving), D6 (enrollment schema).
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ============================================================================
# Course Schemas (FR-04, FR-05, Decision D1, D3)
# ============================================================================


class CourseCreate(BaseModel):
    """Payload for creating a new course (FR-04, Decision D1)."""

    title: str = Field(
        ..., min_length=1, max_length=200, description="Course title (1-200 characters)"
    )
    description: str | None = Field(
        None, max_length=2000, description="Optional course description"
    )
    course_code: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[A-Za-z0-9\-_]+$",
        description="Unique course code (3-50 chars, alphanumeric and hyphens/underscores)",
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Course title cannot be empty or whitespace only")
        return stripped

    @field_validator("course_code")
    @classmethod
    def validate_course_code(cls, v: str) -> str:
        stripped = v.strip().upper()
        if not stripped:
            raise ValueError("Course code cannot be empty or whitespace only")
        return stripped

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            return stripped if stripped else None
        return None

    model_config = ConfigDict(str_strip_whitespace=True)


class CourseUpdate(BaseModel):
    """Payload for partial update of course details or archiving (FR-05, Decision D3)."""

    title: str | None = Field(
        None, min_length=1, max_length=200, description="Updated course title"
    )
    description: str | None = Field(None, max_length=2000, description="Updated course description")
    is_archived: bool | None = Field(None, description="Archive flag for the course")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Course title cannot be empty or whitespace only")
            return stripped
        return None

    model_config = ConfigDict(str_strip_whitespace=True)


class CourseResponse(BaseModel):
    """Public course details response."""

    id: int
    title: str
    description: str | None = None
    course_code: str
    instructor_id: int
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime | None = None
    topic_count: int = 0
    enrollment_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class CourseListResponse(BaseModel):
    """Paginated or complete list of courses."""

    courses: list[CourseResponse]
    total: int


# ============================================================================
# Topic Schemas (FR-06, FR-07)
# ============================================================================


class TopicCreate(BaseModel):
    """Payload for creating a new topic within a course (FR-06)."""

    title: str = Field(
        ..., min_length=1, max_length=200, description="Topic title (1-200 characters)"
    )
    description: str | None = Field(None, max_length=2000, description="Optional topic description")
    order_index: int = Field(default=0, ge=0, description="Sequential ordering position (>= 0)")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Topic title cannot be empty or whitespace only")
        return stripped

    model_config = ConfigDict(str_strip_whitespace=True)


class TopicUpdate(BaseModel):
    """Payload for updating topic details or active status."""

    title: str | None = Field(None, min_length=1, max_length=200, description="Updated topic title")
    description: str | None = Field(None, max_length=2000, description="Updated topic description")
    order_index: int | None = Field(None, ge=0, description="Updated ordering position (>= 0)")
    is_active: bool | None = Field(None, description="Active status of the topic")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Topic title cannot be empty or whitespace only")
            return stripped
        return None

    model_config = ConfigDict(str_strip_whitespace=True)


class TopicResponse(BaseModel):
    """Public topic response with prerequisite summary."""

    id: int
    course_id: int
    title: str
    description: str | None = None
    order_index: int
    is_active: bool = True
    prerequisite_topic_ids: list[int] = Field(
        default_factory=list, description="IDs of direct prerequisite topics"
    )
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TopicListResponse(BaseModel):
    """List of topics belonging to a course."""

    course_id: int
    topics: list[TopicResponse]
    total: int


class TopicReorderItem(BaseModel):
    """Single item in a sequential topic reordering request."""

    topic_id: int = Field(..., ge=1, description="Unique ID of the topic")
    order_index: int = Field(..., ge=0, description="New zero-based sequential order index")


class TopicReorderRequest(BaseModel):
    """Payload for batch topic sequential reordering (FR-07)."""

    topics: list[TopicReorderItem] = Field(
        default_factory=list, description="List of topics with their target order index"
    )
    topic_ids: list[int] | None = Field(
        None, min_length=1, description="Sequential list of topic IDs (index = order)"
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_topic_ids(cls, values: Any) -> Any:
        if (
            isinstance(values, dict)
            and "topic_ids" in values
            and values["topic_ids"] is not None
            and not values.get("topics")
        ):
            values["topics"] = [
                {"topic_id": tid, "order_index": idx} for idx, tid in enumerate(values["topic_ids"])
            ]
        return values

    @field_validator("topics")
    @classmethod
    def validate_unique_topic_ids(cls, v: list[TopicReorderItem]) -> list[TopicReorderItem]:
        if not v:
            raise ValueError("Reordering request must contain at least one topic")
        seen_ids = set()
        seen_indices = set()
        for item in v:
            if item.topic_id in seen_ids:
                raise ValueError(f"Duplicate topic_id {item.topic_id} in reordering request")
            if item.order_index in seen_indices:
                raise ValueError(f"Duplicate order_index {item.order_index} in reordering request")
            seen_ids.add(item.topic_id)
            seen_indices.add(item.order_index)
        return v


# ============================================================================
# Prerequisite Schemas (FR-08, FR-09)
# ============================================================================


class TopicPrerequisiteCreate(BaseModel):
    """Payload for adding a prerequisite dependency to a topic (FR-08)."""

    prerequisite_topic_id: int = Field(
        ...,
        ge=1,
        description="ID of the topic that must be mastered first",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_prereq_id(cls, values: Any) -> Any:
        if (
            isinstance(values, dict)
            and "prerequisite_topic_id" not in values
            and "prerequisite_id" in values
        ):
            values["prerequisite_topic_id"] = values["prerequisite_id"]
        return values


class TopicPrerequisiteResponse(BaseModel):
    """Response representing an established prerequisite dependency edge."""

    id: int
    topic_id: int
    prerequisite_topic_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Enrollment Schemas (FR-10, Decision D6)
# ============================================================================


class EnrollmentRequest(BaseModel):
    """Payload for student self-enrollment by course code (FR-10)."""

    course_code: str | None = Field(
        None, min_length=1, max_length=50, description="Optional course code to verify"
    )

    @field_validator("course_code")
    @classmethod
    def validate_course_code(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip().upper()
            if not stripped:
                raise ValueError("Course code cannot be empty or whitespace only")
            return stripped
        return None

    model_config = ConfigDict(str_strip_whitespace=True)


class EnrollmentResponse(BaseModel):
    """Response returned upon successful course enrollment (Decision D6)."""

    id: int
    student_id: int
    course_id: int

    model_config = ConfigDict(from_attributes=True)


class UserEnrollmentsResponse(BaseModel):
    """List of all courses an individual student is enrolled in."""

    student_id: int
    enrolled_courses: list[CourseResponse]
    total: int
