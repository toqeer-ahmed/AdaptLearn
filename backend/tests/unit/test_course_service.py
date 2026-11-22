"""Unit tests for CourseService and CourseRepository (AdaptLearn M1).

Requirements Traceability:
- FR-04: Course creation, unique code enforcement, instructor ownership.
- FR-05: Course lifecycle, updates, publishing, and archiving (Decision D3).
- FR-06: Topic creation, sequential order indexing.
- FR-07: Atomic topic reordering.
- FR-08: Topic prerequisite management.
- FR-09: Self-prerequisite, cross-course, and circular dependency rejection.
- FR-10: Student enrollment, duplicate prevention, and privacy enforcement.
- Decisions: D1 (course code), D2 (topic deletion restriction), D3 (archived read-only), D6 (enrollment table), D7 (ownership sync).
"""

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.progress import QuestionStatsModel
from app.models.user import UserModel
from app.repositories.course_repository import CourseRepository
from app.repositories.progress_repository import ProgressRepository
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    TopicCreate,
    TopicReorderItem,
    TopicReorderRequest,
)
from app.services.course_service import CourseService


@pytest.fixture
def service_setup():
    """Create isolated in-memory test database, repositories, and CourseService."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Seed users
    with TestingSession() as session:
        instructor1 = UserModel(
            id=1,
            name="Prof. Ada Lovelace",
            email="lovelace@instructor.edu",
            password_hash="hash",
            role="instructor",
            is_active=True,
        )
        instructor2 = UserModel(
            id=2,
            name="Prof. Alan Turing",
            email="turing@instructor.edu",
            password_hash="hash",
            role="instructor",
            is_active=True,
        )
        student1 = UserModel(
            id=3,
            name="Grace Hopper",
            email="hopper@student.edu",
            password_hash="hash",
            role="student",
            is_active=True,
        )
        student2 = UserModel(
            id=4,
            name="Linus Torvalds",
            email="torvalds@student.edu",
            password_hash="hash",
            role="student",
            is_active=True,
        )
        session.add_all([instructor1, instructor2, student1, student2])
        session.commit()

    course_repo = CourseRepository(session_factory=TestingSession)
    progress_repo = ProgressRepository(session_factory=TestingSession)
    service = CourseService(course_repo=course_repo, progress_repo=progress_repo)

    return {
        "service": service,
        "course_repo": course_repo,
        "progress_repo": progress_repo,
        "session_factory": TestingSession,
    }


class TestCourseOperations:
    """Validate CourseService course creation, listing, updating, and archiving."""

    def test_create_course_success_as_instructor(self, service_setup):
        """Instructor creates course with unique code and auto-synced ownership (FR-04, D7)."""
        service = service_setup["service"]
        progress_repo = service_setup["progress_repo"]

        payload = CourseCreate(
            title="Software Architecture",
            description="Enterprise patterns.",
            course_code="cs-arch-2026",
        )
        course = service.create_course(payload, current_user_id=1, current_user_role="instructor")

        assert course.id is not None
        assert course.title == "Software Architecture"
        assert course.course_code == "CS-ARCH-2026"
        assert course.instructor_id == 1
        assert course.is_archived is False

        # Verify ownership synced to M5 ProgressRepository
        assert progress_repo.is_course_owner(course.id, instructor_id=1) is True

    def test_create_course_forbidden_for_student(self, service_setup):
        """Students cannot author courses (FR-04)."""
        service = service_setup["service"]
        payload = CourseCreate(title="Invalid Course", course_code="CS-INVALID")

        with pytest.raises(HTTPException) as exc:
            service.create_course(payload, current_user_id=3, current_user_role="student")
        assert exc.value.status_code == 403

    def test_create_course_duplicate_code_conflict(self, service_setup):
        """Duplicate course code raises HTTP 409 Conflict (FR-04, Decision D1)."""
        service = service_setup["service"]
        p1 = CourseCreate(title="Course 1", course_code="UNIQUE-101")
        service.create_course(p1, current_user_id=1, current_user_role="instructor")

        p2 = CourseCreate(title="Course 2", course_code="unique-101")
        with pytest.raises(HTTPException) as exc:
            service.create_course(p2, current_user_id=1, current_user_role="instructor")
        assert exc.value.status_code == 409

    def test_get_course_details(self, service_setup):
        """Retrieve course details by ID."""
        service = service_setup["service"]
        payload = CourseCreate(title="Data Structures", course_code="CS-DS-101")
        created = service.create_course(payload, current_user_id=1, current_user_role="instructor")

        retrieved = service.get_course(created.id)
        assert retrieved.id == created.id
        assert retrieved.title == "Data Structures"

    def test_get_nonexistent_course_404(self, service_setup):
        """Retrieving nonexistent course raises HTTP 404."""
        service = service_setup["service"]
        with pytest.raises(HTTPException) as exc:
            service.get_course(9999)
        assert exc.value.status_code == 404

    def test_update_course_success_as_owner(self, service_setup):
        """Course owner can update title and description."""
        service = service_setup["service"]
        c = service.create_course(
            CourseCreate(title="Old Title", course_code="CS-UPD"),
            current_user_id=1,
            current_user_role="instructor",
        )
        updated = service.update_course(
            c.id,
            CourseUpdate(title="New Title", description="New Desc"),
            current_user_id=1,
            current_user_role="instructor",
        )
        assert updated.title == "New Title"
        assert updated.description == "New Desc"

    def test_update_course_forbidden_for_non_owner(self, service_setup):
        """Non-owner instructor cannot update course."""
        service = service_setup["service"]
        c = service.create_course(
            CourseCreate(title="Owned Course", course_code="CS-OWNED"),
            current_user_id=1,
            current_user_role="instructor",
        )
        with pytest.raises(HTTPException) as exc:
            service.update_course(
                c.id,
                CourseUpdate(title="Hacked Title"),
                current_user_id=2,  # Instructor 2
                current_user_role="instructor",
            )
        assert exc.value.status_code == 403

    def test_archiving_and_publishing_lifecycle(self, service_setup):
        """Owner can archive and re-publish courses (Decision D3)."""
        service = service_setup["service"]
        c = service.create_course(
            CourseCreate(title="Lifecycle Course", course_code="CS-LIFE"),
            current_user_id=1,
            current_user_role="instructor",
        )
        assert c.is_archived is False

        # Archive
        archived = service.archive_course(c.id, current_user_id=1, current_user_role="instructor")
        assert archived.is_archived is True

        # Editing title of archived course is rejected
        with pytest.raises(HTTPException) as exc:
            service.update_course(
                c.id,
                CourseUpdate(title="Illegal Edit"),
                current_user_id=1,
                current_user_role="instructor",
            )
        assert exc.value.status_code == 400

        # Publish
        published = service.publish_course(c.id, current_user_id=1, current_user_role="instructor")
        assert published.is_archived is False

    def test_archived_course_read_only_access_rules(self, service_setup):
        """Archived course is accessible only to enrolled students and owner (Decision D3)."""
        service = service_setup["service"]
        c = service.create_course(
            CourseCreate(title="Archived Access", course_code="CS-ARCH-ACC"),
            current_user_id=1,
            current_user_role="instructor",
        )
        # Student 3 enrolls before archiving
        service.enroll_student(c.id, student_id=3, current_user_id=3, current_user_role="student")
        service.archive_course(c.id, current_user_id=1, current_user_role="instructor")

        # Enrolled student can read historical course
        assert service.get_course(c.id, current_user_id=3, current_user_role="student").id == c.id

        # Unenrolled student (Student 4) is forbidden (HTTP 403)
        with pytest.raises(HTTPException) as exc:
            service.get_course(c.id, current_user_id=4, current_user_role="student")
        assert exc.value.status_code == 403

        # Non-owner instructor (Instructor 2) is forbidden (HTTP 403)
        with pytest.raises(HTTPException) as exc2:
            service.get_course(c.id, current_user_id=2, current_user_role="instructor")
        assert exc2.value.status_code == 403


class TestTopicOperations:
    """Validate TopicService topic creation, reordering, deletion, and prerequisites."""

    def test_create_and_list_topics(self, service_setup):
        """Owner can create sequential topics; listed in order_index order (FR-06)."""
        service = service_setup["service"]
        c = service.create_course(
            CourseCreate(title="Topic Course", course_code="CS-TOP-1"),
            current_user_id=1,
            current_user_role="instructor",
        )
        service.create_topic(
            c.id,
            TopicCreate(title="Topic 1", order_index=0),
            current_user_id=1,
            current_user_role="instructor",
        )
        service.create_topic(
            c.id,
            TopicCreate(title="Topic 2", order_index=1),
            current_user_id=1,
            current_user_role="instructor",
        )

        topic_list = service.list_course_topics(c.id)
        assert topic_list.total == 2
        assert [t.title for t in topic_list.topics] == ["Topic 1", "Topic 2"]

    def test_create_topic_forbidden_for_non_owner(self, service_setup):
        """Non-owner cannot add topics."""
        service = service_setup["service"]
        c = service.create_course(
            CourseCreate(title="Topic Guard", course_code="CS-TOP-GUARD"),
            current_user_id=1,
            current_user_role="instructor",
        )
        with pytest.raises(HTTPException) as exc:
            service.create_topic(
                c.id,
                TopicCreate(title="Hacked Topic"),
                current_user_id=2,
                current_user_role="instructor",
            )
        assert exc.value.status_code == 403

    def test_atomic_topic_reordering(self, service_setup):
        """Batch topic reordering updates sequential indices cleanly (FR-07)."""
        service = service_setup["service"]
        c = service.create_course(
            CourseCreate(title="Reorder Course", course_code="CS-REORDER"),
            current_user_id=1,
            current_user_role="instructor",
        )
        t1 = service.create_topic(c.id, TopicCreate(title="First", order_index=0), 1, "instructor")
        t2 = service.create_topic(c.id, TopicCreate(title="Second", order_index=1), 1, "instructor")

        # Swap orders: t1 -> 1, t2 -> 0
        reorder_payload = TopicReorderRequest(
            topics=[
                TopicReorderItem(topic_id=t1.id, order_index=1),
                TopicReorderItem(topic_id=t2.id, order_index=0),
            ]
        )
        updated = service.reorder_topics(
            c.id, reorder_payload, current_user_id=1, current_user_role="instructor"
        )
        assert updated.topics[0].id == t2.id
        assert updated.topics[0].order_index == 0
        assert updated.topics[1].id == t1.id
        assert updated.topics[1].order_index == 1

    def test_delete_topic_success(self, service_setup):
        """Topic deletion succeeds when unreferenced by quiz questions."""
        service = service_setup["service"]
        c = service.create_course(
            CourseCreate(title="Delete Course", course_code="CS-DEL-1"),
            current_user_id=1,
            current_user_role="instructor",
        )
        topic = service.create_topic(c.id, TopicCreate(title="Doomed Topic"), 1, "instructor")

        res = service.delete_topic(topic.id, current_user_id=1, current_user_role="instructor")
        assert res["status"] == "success"

        with pytest.raises(HTTPException) as exc:
            service.get_topic(topic.id)
        assert exc.value.status_code == 404

    def test_delete_topic_rejected_when_quiz_questions_exist(self, service_setup):
        """Topic deletion rejected with HTTP 400 if quiz questions reference it (Decision D2)."""
        service = service_setup["service"]
        session_factory = service_setup["session_factory"]

        c = service.create_course(
            CourseCreate(title="Protected Topic Course", course_code="CS-PROT-TOP"),
            current_user_id=1,
            current_user_role="instructor",
        )
        topic = service.create_topic(c.id, TopicCreate(title="Referenced Topic"), 1, "instructor")

        # Seed a quiz question referencing this topic in QuestionStatsModel
        with session_factory() as session:
            q = QuestionStatsModel(
                course_id=c.id,
                question_id=101,
                question_text="What is a design pattern?",
                topic_id=topic.id,
                topic_name=topic.title,
                difficulty="medium",
            )
            session.add(q)
            session.commit()

        # Attempting deletion must be rejected with 400
        with pytest.raises(HTTPException) as exc:
            service.delete_topic(topic.id, current_user_id=1, current_user_role="instructor")
        assert exc.value.status_code == 400
        assert "Decision D2" in exc.value.detail

    def test_prerequisite_graph_and_cycle_detection(self, service_setup):
        """Add prerequisites; reject self-dependencies, cross-course, and circular cycles (FR-08, FR-09)."""
        service = service_setup["service"]
        c1 = service.create_course(
            CourseCreate(title="DAG Course 1", course_code="CS-DAG-1"), 1, "instructor"
        )
        c2 = service.create_course(
            CourseCreate(title="DAG Course 2", course_code="CS-DAG-2"), 1, "instructor"
        )

        tA = service.create_topic(
            c1.id, TopicCreate(title="Topic A", order_index=0), 1, "instructor"
        )
        tB = service.create_topic(
            c1.id, TopicCreate(title="Topic B", order_index=1), 1, "instructor"
        )
        tC = service.create_topic(
            c1.id, TopicCreate(title="Topic C", order_index=2), 1, "instructor"
        )
        tOther = service.create_topic(
            c2.id, TopicCreate(title="Other Course Topic"), 1, "instructor"
        )

        # 1. Valid prerequisite: B requires A
        edge = service.add_prerequisite(
            tB.id, tA.id, current_user_id=1, current_user_role="instructor"
        )
        assert edge.topic_id == tB.id
        assert edge.prerequisite_topic_id == tA.id

        # 2. Self-prerequisite rejected (HTTP 400)
        with pytest.raises(HTTPException) as exc_self:
            service.add_prerequisite(
                tA.id, tA.id, current_user_id=1, current_user_role="instructor"
            )
        assert exc_self.value.status_code == 400

        # 3. Cross-course prerequisite rejected (HTTP 400)
        with pytest.raises(HTTPException) as exc_cross:
            service.add_prerequisite(
                tA.id, tOther.id, current_user_id=1, current_user_role="instructor"
            )
        assert exc_cross.value.status_code == 400

        # 4. Direct cycle rejected: B already requires A. Attempting A requires B
        with pytest.raises(HTTPException) as exc_direct_cycle:
            service.add_prerequisite(
                tA.id, tB.id, current_user_id=1, current_user_role="instructor"
            )
        assert exc_direct_cycle.value.status_code == 400
        assert "Circular prerequisite dependency" in exc_direct_cycle.value.detail

        # 5. Indirect cycle rejected: C requires B (so C -> B -> A). Attempting A requires C
        service.add_prerequisite(tC.id, tB.id, current_user_id=1, current_user_role="instructor")
        with pytest.raises(HTTPException) as exc_indirect_cycle:
            service.add_prerequisite(
                tA.id, tC.id, current_user_id=1, current_user_role="instructor"
            )
        assert exc_indirect_cycle.value.status_code == 400
        assert "Circular prerequisite dependency" in exc_indirect_cycle.value.detail

        # 6. Remove prerequisite
        res = service.remove_prerequisite(
            tB.id, tA.id, current_user_id=1, current_user_role="instructor"
        )
        assert res["status"] == "success"


class TestEnrollmentOperations:
    """Validate student enrollment, duplicate rejection, and privacy rules."""

    def test_student_enrollment_success(self, service_setup):
        """Student successfully enrolls in course (FR-10, Decision D6)."""
        service = service_setup["service"]
        c = service.create_course(
            CourseCreate(title="Enrollment Course", course_code="CS-ENROLL-1"), 1, "instructor"
        )

        enrollment = service.enroll_student(
            course_id=c.id,
            student_id=3,
            current_user_id=3,
            current_user_role="student",
            course_code="CS-ENROLL-1",
        )
        assert enrollment.student_id == 3
        assert enrollment.course_id == c.id

        # Verify course roster
        roster = service.get_course_students(
            c.id, current_user_id=1, current_user_role="instructor"
        )
        assert roster == [3]

    def test_enrollment_rejected_for_non_student(self, service_setup):
        """Instructors cannot enroll as students."""
        service = service_setup["service"]
        c = service.create_course(
            CourseCreate(title="Course", course_code="CS-ROLE"), 1, "instructor"
        )

        with pytest.raises(HTTPException) as exc:
            service.enroll_student(
                c.id, student_id=1, current_user_id=1, current_user_role="instructor"
            )
        assert exc.value.status_code == 403

    def test_student_cannot_enroll_another_student(self, service_setup):
        """Student privacy: Student 3 cannot enroll Student 4."""
        service = service_setup["service"]
        c = service.create_course(
            CourseCreate(title="Privacy Course", course_code="CS-PRIV"), 1, "instructor"
        )

        with pytest.raises(HTTPException) as exc:
            service.enroll_student(
                c.id, student_id=4, current_user_id=3, current_user_role="student"
            )
        assert exc.value.status_code == 403

    def test_duplicate_enrollment_rejected(self, service_setup):
        """Duplicate enrollment returns HTTP 409 Conflict."""
        service = service_setup["service"]
        c = service.create_course(
            CourseCreate(title="Dup Course", course_code="CS-DUP"), 1, "instructor"
        )

        service.enroll_student(c.id, student_id=3, current_user_id=3, current_user_role="student")

        with pytest.raises(HTTPException) as exc:
            service.enroll_student(
                c.id, student_id=3, current_user_id=3, current_user_role="student"
            )
        assert exc.value.status_code == 409

    def test_enrollment_in_archived_course_rejected(self, service_setup):
        """Cannot enroll in an archived course (HTTP 400)."""
        service = service_setup["service"]
        c = service.create_course(
            CourseCreate(title="Archived", course_code="CS-ARCH-DIS"), 1, "instructor"
        )
        service.archive_course(c.id, current_user_id=1, current_user_role="instructor")

        with pytest.raises(HTTPException) as exc:
            service.enroll_student(
                c.id, student_id=3, current_user_id=3, current_user_role="student"
            )
        assert exc.value.status_code == 400

    def test_enrollment_with_mismatched_course_code_rejected(self, service_setup):
        """Enrollment with incorrect course code raises HTTP 400."""
        service = service_setup["service"]
        c = service.create_course(
            CourseCreate(title="Code Check", course_code="CS-MATCH"), 1, "instructor"
        )

        with pytest.raises(HTTPException) as exc:
            service.enroll_student(
                c.id,
                student_id=3,
                current_user_id=3,
                current_user_role="student",
                course_code="WRONG-CODE",
            )
        assert exc.value.status_code == 400

    def test_student_enrollments_listing_privacy(self, service_setup):
        """Student can view their own enrollments; viewing another student's is forbidden."""
        service = service_setup["service"]
        c1 = service.create_course(
            CourseCreate(title="C1", course_code="COURSE-01"), 1, "instructor"
        )
        c2 = service.create_course(
            CourseCreate(title="C2", course_code="COURSE-02"), 1, "instructor"
        )

        service.enroll_student(c1.id, student_id=3, current_user_id=3, current_user_role="student")
        service.enroll_student(c2.id, student_id=3, current_user_id=3, current_user_role="student")

        # Student 3 viewing own enrollments
        enrollments = service.get_student_enrollments(
            student_id=3, current_user_id=3, current_user_role="student"
        )
        assert enrollments.total == 2
        assert len(enrollments.enrolled_courses) == 2

        # Student 4 attempting to view Student 3's enrollments (HTTP 403)
        with pytest.raises(HTTPException) as exc:
            service.get_student_enrollments(
                student_id=3, current_user_id=4, current_user_role="student"
            )
        assert exc.value.status_code == 403
