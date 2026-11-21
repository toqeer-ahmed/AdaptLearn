"""Pydantic schemas for instructor progress analytics (AdaptLearn M5).

Requirements Traceability:
- FR-22: View enrolled students with their mastery level in each topic (Student Roster).
- FR-23: View the number of students at each mastery level per topic (Mastery Distribution).
- FR-24: View question statistics (times answered and correct percentage).
"""

from pydantic import BaseModel, Field


class TopicMasteryDistributionItem(BaseModel):
    """Student count breakdown by mastery level for a specific topic (FR-23)."""
    topic_id: int
    topic_name: str
    weak_count: int = Field(0, description="Students with Weak mastery")
    developing_count: int = Field(0, description="Students with Developing mastery")
    proficient_count: int = Field(0, description="Students with Proficient mastery")
    not_assessed_count: int = Field(0, description="Students not yet assessed")
    total_students: int = Field(0, description="Total enrolled students evaluated")


class MasteryDistributionResponse(BaseModel):
    """Course-wide topic mastery distribution report (FR-23)."""
    course_id: int
    total_enrolled: int
    topics: list[TopicMasteryDistributionItem]


class StudentTopicMasteryItem(BaseModel):
    """An individual student's mastery score and level in a single topic."""
    topic_id: int
    topic_name: str
    score: float
    mastery_level: str


class StudentRosterMasteryItem(BaseModel):
    """Enrolled student record with per-topic mastery status (FR-22)."""
    student_id: int
    student_name: str
    topic_masteries: list[StudentTopicMasteryItem]


class StudentRosterResponse(BaseModel):
    """Enrolled student roster mastery matrix report (FR-22)."""
    course_id: int
    total_students: int
    students: list[StudentRosterMasteryItem]


class QuestionStatItem(BaseModel):
    """Question answering statistics and performance metrics (FR-24)."""
    question_id: int
    question_text: str
    topic_id: int
    topic_name: str
    difficulty: str
    times_answered: int
    correct_count: int
    correct_percentage: float = Field(
        ...,
        description="Percentage of correct answers (0.0 to 100.0)",
    )


class CourseQuestionStatsResponse(BaseModel):
    """Course-level question difficulty and answering analytics report (FR-24)."""
    course_id: int
    total_questions: int
    questions: list[QuestionStatItem]
