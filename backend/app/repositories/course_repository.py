"""Repository for Course, Topic, Prerequisite, and Enrollment persistence (AdaptLearn M1).

Requirements Traceability:
- FR-04: Course persistence, retrieval, code lookups, instructor ownership.
- FR-05: Course lifecycle, updates, and archiving.
- FR-06: Topic creation, retrieval, sequential ordering.
- FR-07: Sequential topic reordering with transactional integrity.
- FR-08: Topic prerequisite edge management.
- FR-09: Prerequisite graph integrity and cycle check helper.
- FR-10: Student course enrollment persistence and lookups.
- Decisions: D1 (course codes), D2 (topic deletion restriction), D3 (archiving), D6 (enrollment table adoption), D7 (instructor ownership).
"""

from sqlalchemy.orm import Session, sessionmaker

from app.db.session import SessionLocal, init_db
from app.models.course import (
    CourseModel,
    EnrollmentModel,
    TopicModel,
    TopicPrerequisiteModel,
    validate_prerequisite_edge,
)
from app.models.progress import QuestionStatsModel


class CourseRepository:
    """SQLAlchemy persistent repository managing courses, topics, prerequisites, and enrollments."""

    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self.session_factory = session_factory or SessionLocal
        init_db()

    # =========================================================================
    # Course Operations (FR-04, FR-05)
    # =========================================================================

    def create_course(
        self,
        title: str,
        course_code: str,
        instructor_id: int,
        description: str | None = None,
    ) -> CourseModel:
        """Create and persist a new course entity."""
        with self.session_factory() as session:
            course = CourseModel(
                title=title,
                course_code=course_code,
                instructor_id=instructor_id,
                description=description,
                is_archived=False,
            )
            session.add(course)
            session.commit()
            session.refresh(course)
            return course

    def get_course_by_id(self, course_id: int) -> CourseModel | None:
        """Retrieve a course by its primary key ID."""
        with self.session_factory() as session:
            return session.query(CourseModel).filter_by(id=course_id).first()

    def get_course_by_code(self, course_code: str) -> CourseModel | None:
        """Retrieve a course by its unique course code (case-insensitive lookup)."""
        with self.session_factory() as session:
            return (
                session.query(CourseModel)
                .filter(CourseModel.course_code.ilike(course_code.strip()))
                .first()
            )

    def list_courses(
        self,
        instructor_id: int | None = None,
        include_archived: bool = True,
    ) -> list[CourseModel]:
        """List all courses, optionally filtered by instructor or archive status."""
        with self.session_factory() as session:
            query = session.query(CourseModel)
            if instructor_id is not None:
                query = query.filter_by(instructor_id=instructor_id)
            if not include_archived:
                query = query.filter_by(is_archived=False)
            return query.order_by(CourseModel.created_at.desc()).all()

    def update_course(
        self,
        course_id: int,
        title: str | None = None,
        description: str | None = None,
        is_archived: bool | None = None,
    ) -> CourseModel | None:
        """Update mutable fields of a course."""
        with self.session_factory() as session:
            course = session.query(CourseModel).filter_by(id=course_id).first()
            if not course:
                return None
            if title is not None:
                course.title = title
            if description is not None:
                course.description = description
            if is_archived is not None:
                course.is_archived = is_archived
            session.commit()
            session.refresh(course)
            return course

    def archive_course(self, course_id: int) -> CourseModel | None:
        """Archive a course, setting is_archived = True."""
        return self.update_course(course_id=course_id, is_archived=True)

    def publish_course(self, course_id: int) -> CourseModel | None:
        """Publish / unarchive a course, setting is_archived = False."""
        return self.update_course(course_id=course_id, is_archived=False)

    # =========================================================================
    # Topic Operations (FR-06, FR-07, FR-08, FR-09)
    # =========================================================================

    def create_topic(
        self,
        course_id: int,
        title: str,
        description: str | None = None,
        order_index: int | None = None,
    ) -> TopicModel:
        """Create and persist a new topic in a course."""
        with self.session_factory() as session:
            if order_index is None:
                max_order = (
                    session.query(TopicModel.order_index)
                    .filter_by(course_id=course_id)
                    .order_by(TopicModel.order_index.desc())
                    .first()
                )
                order_index = (max_order[0] + 1) if max_order else 0

            topic = TopicModel(
                course_id=course_id,
                title=title,
                description=description,
                order_index=order_index,
                is_active=True,
            )
            session.add(topic)
            session.commit()
            session.refresh(topic)
            return topic

    def get_topic_by_id(self, topic_id: int) -> TopicModel | None:
        """Retrieve a topic by ID including loaded prerequisites."""
        with self.session_factory() as session:
            return session.query(TopicModel).filter_by(id=topic_id).first()

    def list_course_topics(
        self,
        course_id: int,
        active_only: bool = False,
    ) -> list[TopicModel]:
        """Retrieve all topics for a course ordered sequentially by order_index."""
        with self.session_factory() as session:
            query = session.query(TopicModel).filter_by(course_id=course_id)
            if active_only:
                query = query.filter_by(is_active=True)
            return query.order_by(TopicModel.order_index.asc()).all()

    def update_topic(
        self,
        topic_id: int,
        title: str | None = None,
        description: str | None = None,
        order_index: int | None = None,
        is_active: bool | None = None,
    ) -> TopicModel | None:
        """Update mutable fields of a topic."""
        with self.session_factory() as session:
            topic = session.query(TopicModel).filter_by(id=topic_id).first()
            if not topic:
                return None
            if title is not None:
                topic.title = title
            if description is not None:
                topic.description = description
            if order_index is not None:
                topic.order_index = order_index
            if is_active is not None:
                topic.is_active = is_active
            session.commit()
            session.refresh(topic)
            return topic

    def delete_topic(self, topic_id: int) -> bool:
        """Delete a topic and cascade remove associated edges."""
        with self.session_factory() as session:
            topic = session.query(TopicModel).filter_by(id=topic_id).first()
            if not topic:
                return False
            session.delete(topic)
            session.commit()
            return True

    def reorder_topics(
        self,
        course_id: int,
        topic_orders: list[tuple[int, int]],
    ) -> list[TopicModel]:
        """Atomically update order_index values for topics within a course (FR-07)."""
        with self.session_factory() as session:
            # Shift order_indices to temporary negative values to avoid unique constraint collisions
            for topic_id, new_order in topic_orders:
                session.query(TopicModel).filter_by(id=topic_id, course_id=course_id).update(
                    {"order_index": -1000 - new_order}
                )
            session.flush()

            # Apply final sequential order_index values
            for topic_id, new_order in topic_orders:
                session.query(TopicModel).filter_by(id=topic_id, course_id=course_id).update(
                    {"order_index": new_order}
                )
            session.commit()

            return (
                session.query(TopicModel)
                .filter_by(course_id=course_id)
                .order_by(TopicModel.order_index.asc())
                .all()
            )

    def add_prerequisite(
        self,
        topic_id: int,
        prerequisite_topic_id: int,
    ) -> TopicPrerequisiteModel:
        """Add a directed prerequisite edge after graph validation (FR-08, FR-09)."""
        with self.session_factory() as session:
            validate_prerequisite_edge(session, topic_id, prerequisite_topic_id)
            edge = TopicPrerequisiteModel(
                topic_id=topic_id,
                prerequisite_topic_id=prerequisite_topic_id,
            )
            session.add(edge)
            session.commit()
            session.refresh(edge)
            return edge

    def remove_prerequisite(
        self,
        topic_id: int,
        prerequisite_topic_id: int,
    ) -> bool:
        """Remove a directed prerequisite edge."""
        with self.session_factory() as session:
            edge = (
                session.query(TopicPrerequisiteModel)
                .filter_by(topic_id=topic_id, prerequisite_topic_id=prerequisite_topic_id)
                .first()
            )
            if not edge:
                return False
            session.delete(edge)
            session.commit()
            return True

    def get_prerequisites_for_topic(self, topic_id: int) -> list[int]:
        """Return list of prerequisite topic IDs that must be completed before topic_id."""
        with self.session_factory() as session:
            rows = (
                session.query(TopicPrerequisiteModel.prerequisite_topic_id)
                .filter_by(topic_id=topic_id)
                .all()
            )
            return [r[0] for r in rows]

    def has_quiz_questions(self, topic_id: int) -> bool:
        """Check if any quiz questions reference this topic (Decision D2)."""
        with self.session_factory() as session:
            return (
                session.query(QuestionStatsModel).filter_by(topic_id=topic_id).first() is not None
            )

    # =========================================================================
    # Enrollment Operations (FR-10, Decision D6)
    # =========================================================================

    def enroll_student(self, student_id: int, course_id: int) -> EnrollmentModel:
        """Record student enrollment in course_enrollments."""
        with self.session_factory() as session:
            existing = (
                session.query(EnrollmentModel)
                .filter_by(student_id=student_id, course_id=course_id)
                .first()
            )
            if existing:
                return existing
            enrollment = EnrollmentModel(student_id=student_id, course_id=course_id)
            session.add(enrollment)
            session.commit()
            session.refresh(enrollment)
            return enrollment

    def is_student_enrolled(self, student_id: int, course_id: int) -> bool:
        """Check if student is enrolled in a course."""
        with self.session_factory() as session:
            return (
                session.query(EnrollmentModel)
                .filter_by(student_id=student_id, course_id=course_id)
                .first()
                is not None
            )

    def get_enrollment(self, student_id: int, course_id: int) -> EnrollmentModel | None:
        """Retrieve enrollment record for student and course."""
        with self.session_factory() as session:
            return (
                session.query(EnrollmentModel)
                .filter_by(student_id=student_id, course_id=course_id)
                .first()
            )

    def get_student_enrolled_courses(self, student_id: int) -> list[CourseModel]:
        """Retrieve list of courses a student is enrolled in."""
        with self.session_factory() as session:
            enrollments = session.query(EnrollmentModel).filter_by(student_id=student_id).all()
            course_ids = [e.course_id for e in enrollments]
            if not course_ids:
                return []
            return (
                session.query(CourseModel)
                .filter(CourseModel.id.in_(course_ids))
                .order_by(CourseModel.title.asc())
                .all()
            )

    def get_course_enrolled_students(self, course_id: int) -> list[int]:
        """Retrieve list of student IDs enrolled in a course."""
        with self.session_factory() as session:
            rows = session.query(EnrollmentModel.student_id).filter_by(course_id=course_id).all()
            return sorted([r[0] for r in rows])

    def clear(self) -> None:
        """Utility for test suites to cleanly purge all M1 table records."""
        with self.session_factory() as session:
            session.query(TopicPrerequisiteModel).delete()
            session.query(TopicModel).delete()
            session.query(EnrollmentModel).delete()
            session.query(CourseModel).delete()
            session.commit()


# Global singleton instance for dependency injection
_global_course_repo: CourseRepository | None = None


def get_course_repository() -> CourseRepository:
    """Retrieve the global CourseRepository singleton instance."""
    global _global_course_repo
    if _global_course_repo is None:
        _global_course_repo = CourseRepository()
    return _global_course_repo
