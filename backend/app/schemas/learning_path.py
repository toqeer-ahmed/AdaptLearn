"""Pydantic schemas for Module 4: Personalized Learning Paths (AdaptLearn M4).

Requirements Traceability:
- FR-18: Display ordered, prerequisite-aware learning path with mastery status per topic.
- FR-19: Pedagogical recommendation rationale per recommended topic.
- FR-20: Cold-start support for students with no prior attempt history.
- FR-25: Defensive Pydantic v2 validation contracts with extra='forbid'.
- Decision 4: 'Proficient' mastery level (>= 0.80) is the prerequisite-unlock threshold.
- Decision 5: Instructor may supply ?student_id query param to view a specific student's path.
"""

from pydantic import BaseModel, ConfigDict, Field


class TopicPathItem(BaseModel):
    """Represents one topic in the personalized learning path.

    Attributes:
        topic_id: Unique identifier of the topic.
        title: Display name of the topic.
        description: Optional descriptive text for the topic.
        order_index: Position of the topic in the course syllabus (0-based).
        status: Current mastery level: 'Proficient', 'Developing', 'Weak', or 'Not Assessed'.
        score: Difficulty-weighted mastery score in [0.0, 1.0].
        is_unlocked: True when all prerequisite topics are Proficient (or topic has none).
        is_recommended: True when the M3 recommendation engine selected this topic.
        locked_reason: Human-readable explanation for why the topic is locked, if applicable.
        prerequisite_topic_ids: Ordered list of prerequisite topic IDs for this topic.
        rationale: Pedagogical explanation from recommendation engine (FR-19), if recommended.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    topic_id: int = Field(..., description="Unique topic identifier")
    title: str = Field(..., description="Topic display name")
    description: str | None = Field(None, description="Optional topic description")
    order_index: int = Field(..., description="Position in course syllabus (0-based)")
    status: str = Field(
        ...,
        description="Mastery level: Proficient | Developing | Weak | Not Assessed",
    )
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Difficulty-weighted mastery score [0.0, 1.0]",
    )
    is_unlocked: bool = Field(
        ...,
        description="True when all prerequisites are Proficient or topic has no prerequisites",
    )
    is_recommended: bool = Field(
        ...,
        description="True when M3 recommendation engine selected this topic",
    )
    locked_reason: str | None = Field(
        None,
        description="Explanation of why topic is locked (only set when is_unlocked=False)",
    )
    prerequisite_topic_ids: list[int] = Field(
        default_factory=list,
        description="IDs of prerequisite topics for this topic",
    )
    rationale: str | None = Field(
        None,
        description="Pedagogical rationale from recommendation engine (FR-19)",
    )


class LearningPathResponse(BaseModel):
    """Full personalized learning path response for a student in a course.

    Attributes:
        course_id: Identifier of the course.
        student_id: Identifier of the student this path belongs to.
        total_topics: Total number of topics in the course.
        unlocked_count: Number of topics currently unlocked (prerequisites met).
        completed_count: Number of topics with Proficient mastery level.
        completion_percentage: Percentage of topics completed [0.0, 100.0].
        path: Ordered list of TopicPathItem objects representing the learning path.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    course_id: int = Field(..., description="Course identifier")
    student_id: int = Field(..., description="Student this learning path belongs to")
    total_topics: int = Field(..., ge=0, description="Total topics in the course")
    unlocked_count: int = Field(..., ge=0, description="Topics with prerequisites met")
    completed_count: int = Field(..., ge=0, description="Topics at Proficient mastery")
    completion_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of topics completed (Proficient) [0.0, 100.0]",
    )
    path: list[TopicPathItem] = Field(
        default_factory=list,
        description="Ordered list of topic path items",
    )
