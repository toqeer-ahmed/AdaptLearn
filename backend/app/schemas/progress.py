"""Pydantic schemas for student progress, dashboard, and attempt history (AdaptLearn M5).

Requirements Traceability:
- FR-15: Attempt history listing and pagination.
- FR-21: Student dashboard response consolidating mastery, recommendations, and recent attempts.
"""

from pydantic import BaseModel, Field

from app.schemas.adaptive import TopicRecommendationResponse


class TopicProgressItem(BaseModel):
    """Progress status for an individual topic within a course."""
    topic_id: int
    topic_name: str
    score: float
    mastery_level: str


class AttemptSummaryItem(BaseModel):
    """Summary of a single submitted quiz attempt (FR-15, FR-21)."""
    attempt_id: int
    quiz_id: int
    quiz_title: str
    score: float
    total_questions: int
    submitted_at: str


class StudentProgressResponse(BaseModel):
    """Consolidated student progress dashboard response for a course (FR-21)."""
    course_id: int
    student_id: int
    completion_percentage: float = Field(
        ...,
        description="Percentage of course topics classified as Proficient (0.0 to 100.0)",
    )
    topic_breakdown: list[TopicProgressItem] = Field(
        ...,
        description="Mastery score and level for each course topic",
    )
    recommended_topics: list[TopicRecommendationResponse] = Field(
        ...,
        description="Ordered recommended topics with pedagogical rationale (FR-18, FR-19)",
    )
    recent_attempts: list[AttemptSummaryItem] = Field(
        ...,
        description="Most recent quiz attempts in this course",
    )


class AttemptHistoryResponse(BaseModel):
    """Paginated attempt history for an enrolled student (FR-15)."""
    course_id: int
    student_id: int
    total_attempts: int
    page: int
    page_size: int
    attempts: list[AttemptSummaryItem]
