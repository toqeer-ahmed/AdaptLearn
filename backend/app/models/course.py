"""SQLAlchemy ORM models for Module 1: User & Course Management.

Requirements Traceability:
- FR-04: Course creation, unique course codes, instructor ownership.
- FR-05: Course lifecycle, editing, and archiving.
- FR-06: Topic creation, sequential order indexing.
- FR-07: Sequential topic reordering.
- FR-08: Topic prerequisite relationships and dependencies.
- FR-09: Prerequisite graph integrity, cycle prevention, cross-course isolation.
- FR-10: Student course enrollment.
- Decisions: D1 (course code), D2 (topic deletion), D3 (archiving), D6 (enrollment table), D7 (instructor ownership), D10 (M1 core).
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Session, relationship, validates

from app.db.base import Base


class CourseModel(Base):
    """Authoritative course entity (FR-04, FR-05, Decisions D1, D3, D7)."""

    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    course_code = Column(String(50), nullable=False, unique=True, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_archived = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    instructor = relationship("UserModel", backref="authored_courses")
    topics = relationship(
        "TopicModel",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="TopicModel.order_index",
    )
    enrollments = relationship(
        "EnrollmentModel",
        back_populates="course",
        cascade="all, delete-orphan",
    )


class TopicModel(Base):
    """Authoritative course topic entity (FR-06, FR-07, Decisions D2, D10)."""

    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False, default=0, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    course = relationship("CourseModel", back_populates="topics")
    prerequisites = relationship(
        "TopicPrerequisiteModel",
        foreign_keys="TopicPrerequisiteModel.topic_id",
        back_populates="topic",
        cascade="all, delete-orphan",
    )
    required_by = relationship(
        "TopicPrerequisiteModel",
        foreign_keys="TopicPrerequisiteModel.prerequisite_topic_id",
        back_populates="prerequisite_topic",
        cascade="all, delete-orphan",
    )

    __table_args__ = (UniqueConstraint("course_id", "order_index", name="uq_course_topic_order"),)

    def add_prerequisite(self, prereq: "TopicModel", session: Session) -> "TopicPrerequisiteModel":
        """Add a prerequisite topic to this topic, validating same-course and DAG constraints."""
        validate_prerequisite_edge(session, self.id, prereq.id)
        edge = TopicPrerequisiteModel(topic_id=self.id, prerequisite_topic_id=prereq.id)
        session.add(edge)
        return edge


class TopicPrerequisiteModel(Base):
    """Directed edge representing prerequisite dependencies between topics (FR-08, FR-09)."""

    __tablename__ = "topic_prerequisites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(
        Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prerequisite_topic_id = Column(
        Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    topic = relationship("TopicModel", foreign_keys=[topic_id], back_populates="prerequisites")
    prerequisite_topic = relationship(
        "TopicModel", foreign_keys=[prerequisite_topic_id], back_populates="required_by"
    )

    __table_args__ = (
        UniqueConstraint("topic_id", "prerequisite_topic_id", name="uq_topic_prerequisite_edge"),
        CheckConstraint("topic_id != prerequisite_topic_id", name="chk_no_self_prerequisite"),
    )

    @validates("prerequisite_topic_id")
    def validate_prereq_id(self, key: str, value: int) -> int:
        """Reject self-prerequisite immediately at the model level."""
        if self.topic_id is not None and value == self.topic_id:
            raise ValueError("A topic cannot be a prerequisite of itself.")
        return value

    @validates("topic_id")
    def validate_topic_id(self, key: str, value: int) -> int:
        """Reject self-prerequisite immediately at the model level."""
        if self.prerequisite_topic_id is not None and value == self.prerequisite_topic_id:
            raise ValueError("A topic cannot be a prerequisite of itself.")
        return value


class EnrollmentModel(Base):
    """Student course enrollment record conforming to Decision D6.

    Adopts exact table name and columns required by M5 ProgressRepository.
    """

    __tablename__ = "course_enrollments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id = Column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    course = relationship("CourseModel", back_populates="enrollments")
    student = relationship("UserModel", backref="course_enrollments")

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course_enrollment"),
    )


def validate_prerequisite_edge(
    session: Session,
    topic_id: int,
    prerequisite_topic_id: int,
) -> None:
    """Validate that adding a prerequisite edge preserves graph integrity.

    Enforces:
    1. No self-prerequisite (topic_id != prerequisite_topic_id).
    2. Same-course invariant (both topics must belong to the same course).
    3. Directed Acyclic Graph (DAG) invariant (no circular dependencies).

    Raises:
        ValueError: If any validation rule is violated.
    """
    if topic_id == prerequisite_topic_id:
        raise ValueError("A topic cannot be a prerequisite of itself.")

    topic = session.query(TopicModel).filter_by(id=topic_id).first()
    prereq = session.query(TopicModel).filter_by(id=prerequisite_topic_id).first()

    if not topic or not prereq:
        raise ValueError("Both topic and prerequisite topic must exist.")

    if topic.course_id != prereq.course_id:
        raise ValueError(
            f"Cross-course prerequisites are not permitted: topic {topic_id} is in course "
            f"{topic.course_id}, but prerequisite {prerequisite_topic_id} is in course {prereq.course_id}."
        )

    # Cycle Detection: DFS traversal to verify prerequisite_topic_id cannot reach topic_id
    visited = set()
    stack = [prerequisite_topic_id]

    while stack:
        current_id = stack.pop()
        if current_id == topic_id:
            raise ValueError(
                f"Circular prerequisite dependency detected: adding prerequisite {prerequisite_topic_id} "
                f"to topic {topic_id} creates a cycle in the prerequisite graph."
            )
        if current_id not in visited:
            visited.add(current_id)
            upstream_edges = (
                session.query(TopicPrerequisiteModel.prerequisite_topic_id)
                .filter_by(topic_id=current_id)
                .all()
            )
            for (upstream_id,) in upstream_edges:
                if upstream_id not in visited:
                    stack.append(upstream_id)
