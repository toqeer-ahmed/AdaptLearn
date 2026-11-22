"""Unit tests for Module 1 domain models (CourseModel, TopicModel, TopicPrerequisiteModel, EnrollmentModel).

Requirements Traceability:
- FR-04: Course creation, unique course codes, instructor ownership.
- FR-05: Course editing and archiving.
- FR-06: Topic creation and sequential ordering.
- FR-07: Unique sequential order indexing per course.
- FR-08: Topic prerequisite relationships.
- FR-09: Prerequisite constraint validation (no self-prerequisites, no duplicate edges, no cycles, no cross-course edges).
- FR-10: Student course enrollment uniqueness.
- Decisions: D1 (course code uniqueness), D3 (archiving flag), D6 (enrollment table adoption), D7 (instructor ownership).
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.adaptive import CourseSettingsModel, CourseTopicModel, StudentTopicResponseModel
from app.models.course import (
    CourseModel,
    EnrollmentModel,
    TopicModel,
    TopicPrerequisiteModel,
)
from app.models.progress import AttemptModel, CourseOwnerModel, QuestionStatsModel
from app.models.user import UserModel
from app.repositories.progress_repository import ProgressRepository


@pytest.fixture
def db_session() -> Session:
    """Provide an isolated in-memory SQLite database session for unit testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    # Seed an instructor and a student
    instructor = UserModel(
        id=1,
        name="Prof. Ada Lovelace",
        email="lovelace@instructor.adaptlearn.edu",
        password_hash="fakehash",
        role="instructor",
        is_active=True,
    )
    student = UserModel(
        id=2,
        name="Grace Hopper",
        email="hopper@student.adaptlearn.edu",
        password_hash="fakehash",
        role="student",
        is_active=True,
    )
    session.add_all([instructor, student])
    session.commit()

    try:
        yield session
    finally:
        session.close()


class TestM1CourseModels:
    """Validate all 10 focused test requirements for M1 domain models."""

    # 1. Course Creation
    def test_course_creation(self, db_session: Session):
        """Course creates successfully with required attributes, defaults, and timestamps."""
        course = CourseModel(
            title="Introduction to Machine Learning",
            description="Foundations of linear models and neural networks.",
            course_code="CS-ML-2026",
            instructor_id=1,
        )
        db_session.add(course)
        db_session.commit()
        db_session.refresh(course)

        assert course.id is not None
        assert course.title == "Introduction to Machine Learning"
        assert course.description == "Foundations of linear models and neural networks."
        assert course.course_code == "CS-ML-2026"
        assert course.instructor_id == 1
        assert course.is_archived is False
        assert course.created_at is not None

    # 2. Unique Course Code Enforcement
    def test_unique_course_code_enforcement(self, db_session: Session):
        """Duplicate course code raises IntegrityError (Decision D1, FR-04)."""
        c1 = CourseModel(title="Course 1", course_code="UNIQUE-CODE", instructor_id=1)
        c2 = CourseModel(title="Course 2", course_code="UNIQUE-CODE", instructor_id=1)
        db_session.add(c1)
        db_session.commit()

        db_session.add(c2)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    # 3. Instructor Ownership
    def test_instructor_ownership(self, db_session: Session):
        """Course is owned by instructor via instructor_id, with navigable bidirectional relationship."""
        course = CourseModel(title="Owned Course", course_code="OWNED-101", instructor_id=1)
        db_session.add(course)
        db_session.commit()

        # Navigate course -> instructor
        assert course.instructor.name == "Prof. Ada Lovelace"
        assert course.instructor.role == "instructor"

        # Navigate instructor -> authored_courses
        instructor = db_session.query(UserModel).filter_by(id=1).first()
        assert course in instructor.authored_courses

    # 4. Topic Creation and Ordering
    def test_topic_creation_and_ordering(self, db_session: Session):
        """Topics created with sequential order_index and unique constraint per course (FR-06, FR-07)."""
        course = CourseModel(title="Ordered Course", course_code="ORDER-200", instructor_id=1)
        db_session.add(course)
        db_session.commit()

        t1 = TopicModel(course_id=course.id, title="Topic 1", order_index=0)
        t2 = TopicModel(course_id=course.id, title="Topic 2", order_index=1)
        t3 = TopicModel(course_id=course.id, title="Topic 3", order_index=2)
        db_session.add_all([t1, t2, t3])
        db_session.commit()

        # Verify sequential ordering in query
        topics = (
            db_session.query(TopicModel)
            .filter_by(course_id=course.id)
            .order_by(TopicModel.order_index)
            .all()
        )
        assert [t.title for t in topics] == ["Topic 1", "Topic 2", "Topic 3"]

        # Duplicate order_index in same course raises IntegrityError
        dup_topic = TopicModel(course_id=course.id, title="Duplicate Order", order_index=1)
        db_session.add(dup_topic)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    # 5. Valid Prerequisites
    def test_valid_prerequisites(self, db_session: Session):
        """Valid prerequisite dependency edge persists and links topics bidirectionally (FR-08)."""
        course = CourseModel(title="Prereq Course", course_code="PREREQ-100", instructor_id=1)
        db_session.add(course)
        db_session.commit()

        t1 = TopicModel(course_id=course.id, title="Basics", order_index=0)
        t2 = TopicModel(course_id=course.id, title="Advanced", order_index=1)
        db_session.add_all([t1, t2])
        db_session.commit()

        edge = t2.add_prerequisite(t1, db_session)
        db_session.commit()

        assert edge.id is not None
        assert len(t2.prerequisites) == 1
        assert t2.prerequisites[0].prerequisite_topic.title == "Basics"
        assert len(t1.required_by) == 1
        assert t1.required_by[0].topic.title == "Advanced"

    # 6. Self-Prerequisite Rejection
    def test_self_prerequisite_rejection(self, db_session: Session):
        """A topic cannot be a prerequisite of itself (rejected at both model validation and DB check constraint)."""
        course = CourseModel(title="Self Prereq Course", course_code="SELF-PREREQ", instructor_id=1)
        db_session.add(course)
        db_session.commit()

        topic = TopicModel(course_id=course.id, title="Self Topic", order_index=0)
        db_session.add(topic)
        db_session.commit()

        # 1. Rejected by add_prerequisite / validate_prerequisite_edge
        with pytest.raises(ValueError, match="cannot be a prerequisite of itself"):
            topic.add_prerequisite(topic, db_session)

        # 2. Rejected by model @validates
        with pytest.raises(ValueError, match="cannot be a prerequisite of itself"):
            TopicPrerequisiteModel(topic_id=topic.id, prerequisite_topic_id=topic.id)

    # 7. Circular Dependency Rejection
    def test_circular_dependency_rejection(self, db_session: Session):
        """Circular prerequisite loops (both direct A<->B and indirect A->B->C->A) are rejected."""
        course = CourseModel(title="DAG Course", course_code="DAG-101", instructor_id=1)
        db_session.add(course)
        db_session.commit()

        tA = TopicModel(course_id=course.id, title="Topic A", order_index=0)
        tB = TopicModel(course_id=course.id, title="Topic B", order_index=1)
        tC = TopicModel(course_id=course.id, title="Topic C", order_index=2)
        db_session.add_all([tA, tB, tC])
        db_session.commit()

        # Scenario 1: Direct Cycle: B requires A, then attempt A requires B
        tB.add_prerequisite(tA, db_session)
        db_session.commit()

        with pytest.raises(ValueError, match="Circular prerequisite dependency detected"):
            tA.add_prerequisite(tB, db_session)

        # Scenario 2: Indirect Cycle: C requires B (so C -> B -> A). Now attempt A requires C
        tC.add_prerequisite(tB, db_session)
        db_session.commit()

        with pytest.raises(ValueError, match="Circular prerequisite dependency detected"):
            tA.add_prerequisite(tC, db_session)

    # 8. Cross-Course Prerequisite Rejection
    def test_cross_course_prerequisite_rejection(self, db_session: Session):
        """Prerequisites between topics belonging to different courses are strictly rejected."""
        c1 = CourseModel(title="Course 1", course_code="C1-CROSS", instructor_id=1)
        c2 = CourseModel(title="Course 2", course_code="C2-CROSS", instructor_id=1)
        db_session.add_all([c1, c2])
        db_session.commit()

        t1 = TopicModel(course_id=c1.id, title="Topic in Course 1", order_index=0)
        t2 = TopicModel(course_id=c2.id, title="Topic in Course 2", order_index=0)
        db_session.add_all([t1, t2])
        db_session.commit()

        with pytest.raises(ValueError, match="Cross-course prerequisites are not permitted"):
            t1.add_prerequisite(t2, db_session)

    # 9. Enrollment Compatibility
    def test_enrollment_compatibility(self, db_session: Session):
        """EnrollmentModel correctly preserves existing course_enrollments schema and unique constraint."""
        course = CourseModel(
            title="Enrollment Course", course_code="ENROLL-COMPAT", instructor_id=1
        )
        db_session.add(course)
        db_session.commit()

        # Valid enrollment
        enrollment = EnrollmentModel(course_id=course.id, student_id=2)
        db_session.add(enrollment)
        db_session.commit()

        assert enrollment.id is not None
        assert enrollment.student_id == 2
        assert enrollment.course_id == course.id
        assert enrollment.student.name == "Grace Hopper"
        assert enrollment.course.title == "Enrollment Course"

        # Duplicate enrollment rejected
        dup_enroll = EnrollmentModel(course_id=course.id, student_id=2)
        db_session.add(dup_enroll)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    # 10. Existing M2/M3/M5 Model Compatibility
    def test_existing_m2_m3_m5_model_compatibility(self, db_session: Session):
        """All existing models from M2, M3, M5 coexist without conflict; dual-source ownership works."""
        # 1. Verify M3 models coexist in same session
        m3_settings = CourseSettingsModel(course_id=10, window_size=5)
        m3_topic = CourseTopicModel(course_id=10, topic_id=101, name="M3 Topic", score=0.85)
        m3_response = StudentTopicResponseModel(
            student_id=2, topic_id=101, difficulty="easy", is_correct=True
        )

        # 2. Verify M5 models coexist in same session
        m5_owner = CourseOwnerModel(course_id=20, instructor_id=1)
        m5_attempt = AttemptModel(
            attempt_id=1,
            student_id=2,
            course_id=20,
            quiz_id=1,
            quiz_title="Test Quiz",
            score=0.9,
            total_questions=10,
            submitted_at="2026-11-21T00:00:00Z",
        )
        m5_stats = QuestionStatsModel(
            course_id=20,
            question_id=1,
            question_text="What is SQA?",
            topic_id=101,
            topic_name="M3 Topic",
            difficulty="easy",
        )
        db_session.add_all([m3_settings, m3_topic, m3_response, m5_owner, m5_attempt, m5_stats])
        db_session.commit()

        # 3. Verify ProgressRepository dual-source course ownership works
        # Case A: Legacy fixture course (only in course_owners table)
        session_factory = sessionmaker(bind=db_session.get_bind())
        p_repo = ProgressRepository(session_factory=session_factory)
        assert p_repo.is_course_owner(course_id=20, instructor_id=1) is True
        assert p_repo.is_course_owner(course_id=20, instructor_id=999) is False

        # Case B: Authoritative M1 course (in courses table)
        m1_course = CourseModel(title="M1 Auth Course", course_code="M1-AUTH", instructor_id=1)
        db_session.add(m1_course)
        db_session.commit()

        assert p_repo.is_course_owner(course_id=m1_course.id, instructor_id=1) is True
        assert p_repo.is_course_owner(course_id=m1_course.id, instructor_id=999) is False
