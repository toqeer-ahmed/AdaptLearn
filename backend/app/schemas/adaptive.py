"""Pydantic schemas for adaptive engine API contracts (AdaptLearn M3).

Requirements Traceability:
- FR-16: Mastery score recalculation request and response schemas.
- FR-17: Mastery classification levels ('Weak', 'Developing', 'Proficient', 'Not Assessed').
- FR-18 & FR-19: Topic recommendation schemas with score, level, and pedagogical rationale.
- FR-20: Course adaptive settings view and partial update schemas.
"""

from pydantic import BaseModel, Field


class AdaptiveSettingsResponse(BaseModel):
    """Current course adaptive configuration parameters (FR-20)."""
    course_id: int
    window_size: int = Field(..., description="Number of recent responses included in calculation (N)")
    easy_weight: float = Field(..., description="Weight multiplier for Easy questions")
    medium_weight: float = Field(..., description="Weight multiplier for Medium questions")
    hard_weight: float = Field(..., description="Weight multiplier for Hard questions")
    weak_threshold: float = Field(..., description="Upper bound for Weak classification")
    proficient_threshold: float = Field(..., description="Lower bound for Proficient classification")
    min_responses: int = Field(..., description="Minimum responses needed for classification")


class AdaptiveSettingsUpdate(BaseModel):
    """Payload for partial update of course adaptive parameters (FR-20)."""
    window_size: int | None = Field(None, ge=1, description="Window size N (must be >= 1)")
    easy_weight: float | None = Field(None, gt=0.0, description="Easy question weight (> 0)")
    medium_weight: float | None = Field(None, gt=0.0, description="Medium question weight (> 0)")
    hard_weight: float | None = Field(None, gt=0.0, description="Hard question weight (> 0)")
    weak_threshold: float | None = Field(None, ge=0.0, le=1.0, description="Weak threshold in [0.0, 1.0]")
    proficient_threshold: float | None = Field(None, ge=0.0, le=1.0, description="Proficient threshold in [0.0, 1.0]")
    min_responses: int | None = Field(None, ge=1, description="Minimum response count (>= 1)")


class TopicRecommendationResponse(BaseModel):
    """An individual recommended topic with pedagogical rationale (FR-18, FR-19)."""
    topic_id: int
    topic_name: str
    mastery_level: str
    score: float
    rationale: str


class RecommendationListResponse(BaseModel):
    """Ordered collection of recommended topics for a student in a course."""
    course_id: int
    recommendations: list[TopicRecommendationResponse]
    total_recommended: int


class AttemptResponseItem(BaseModel):
    """An individual question response in a submitted attempt."""
    question_id: int
    topic_id: int
    difficulty: str
    is_correct: bool


class AttemptMasteryRecalculateRequest(BaseModel):
    """Request to recalculate mastery across topics after quiz submission (FR-16)."""
    student_id: int
    course_id: int
    responses: list[AttemptResponseItem]


class TopicMasteryItem(BaseModel):
    """Updated mastery status for an individual topic."""
    topic_id: int
    score: float
    level: str
    response_count: int


class AttemptMasteryRecalculateResponse(BaseModel):
    """Summary of recalculated topic masteries after an attempt."""
    student_id: int
    course_id: int
    updated_topics: list[TopicMasteryItem]
