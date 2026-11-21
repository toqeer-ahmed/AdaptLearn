"""SQLAlchemy ORM models for Module 3: Adaptive Learning Engine data."""
from sqlalchemy import Boolean, Column, Float, Integer, String, Text

from app.db.base import Base


class CourseSettingsModel(Base):
    """Course-specific adaptive calculation parameters (FR-20)."""
    __tablename__ = "course_adaptive_settings"

    course_id = Column(Integer, primary_key=True, index=True)
    window_size = Column(Integer, nullable=False, default=5)
    easy_weight = Column(Float, nullable=False, default=1.0)
    medium_weight = Column(Float, nullable=False, default=2.0)
    hard_weight = Column(Float, nullable=False, default=3.0)
    weak_threshold = Column(Float, nullable=False, default=0.50)
    proficient_threshold = Column(Float, nullable=False, default=0.80)
    min_responses = Column(Integer, nullable=False, default=3)


class StudentTopicResponseModel(Base):
    """Historical quiz responses per student and topic (FR-16, TC-16-4)."""
    __tablename__ = "student_topic_responses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False, index=True)
    topic_id = Column(Integer, nullable=False, index=True)
    difficulty = Column(String(20), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)


class CourseTopicModel(Base):
    """Course topic candidates and prerequisite graphs for recommendation strategy."""
    __tablename__ = "course_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, nullable=False, index=True)
    topic_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    mastery_level = Column(String(30), nullable=False, default="Not Assessed")
    score = Column(Float, nullable=False, default=0.0)
    order_index = Column(Integer, nullable=False, default=0)
    prerequisites_json = Column(Text, nullable=False, default="[]")
