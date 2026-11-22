"""Service layer for Course, Topic, Prerequisite, and Enrollment business logic (AdaptLearn M1).

Requirements Traceability:
- FR-04: Course creation, unique course codes, instructor ownership.
- FR-05: Course lifecycle, updates, and archiving.
- FR-06: Topic creation, retrieval, sequential ordering.
- FR-07: Sequential topic reordering with transactional integrity.
- FR-08: Topic prerequisite relationships and dependencies.
- FR-09: Prerequisite graph integrity and cycle detection.
- FR-10: Student course enrollment.
- Decisions: D1 (course codes), D2 (topic deletion restriction), D3 (archiving policy), D6 (enrollment table adoption), D7 (instructor ownership).
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.course import CourseModel, TopicModel
from app.repositories.course_repository import (
    CourseRepository,
    get_course_repository,
)
from app.repositories.progress_repository import (
    ProgressRepository,
    get_progress_repository,
)
from app.schemas.course import (
    CourseCreate,
    CourseListResponse,
    CourseResponse,
    CourseUpdate,
    EnrollmentResponse,
    TopicCreate,
    TopicListResponse,
    TopicPrerequisiteResponse,
    TopicReorderRequest,
    TopicResponse,
    TopicUpdate,
    UserEnrollmentsResponse,
)


class CourseService:
    """Business logic coordinator for Module 1."""

    def __init__(
        self,
        course_repo: CourseRepository | None = None,
        progress_repo: ProgressRepository | None = None,
    ) -> None:
        self.course_repo = course_repo or get_course_repository()
        self.progress_repo = progress_repo or get_progress_repository()

    # =========================================================================
    # Course Operations (FR-04, FR-05, Decisions D1, D3, D7)
    # =========================================================================

    def create_course(
        self,
        payload: CourseCreate,
        current_user_id: int,
        current_user_role: str,
    ) -> CourseResponse:
        """Create a new course. Only instructors can author courses (FR-04)."""
        if current_user_role.lower() != "instructor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Only instructors can create courses",
            )

        existing = self.course_repo.get_course_by_code(payload.course_code)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Course code '{payload.course_code}' is already registered",
            )

        course = self.course_repo.create_course(
            title=payload.title,
            course_code=payload.course_code,
            instructor_id=current_user_id,
            description=payload.description,
        )

        # Synchronize course ownership with M5 ProgressRepository (Decision D7)
        self.progress_repo.set_course_owner(
            course_id=course.id,
            instructor_id=current_user_id,
        )

        return self._to_course_response(course)

    def get_course(
        self,
        course_id: int,
        current_user_id: int | None = None,
        current_user_role: str | None = None,
    ) -> CourseResponse:
        """Retrieve a course by ID, enforcing archived visibility policy (Decision D3)."""
        course = self.course_repo.get_course_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found",
            )

        # Decision D3: If course is archived, verify read-only access
        if course.is_archived and current_user_id is not None:
            if current_user_role and current_user_role.lower() == "student":
                is_enrolled = self.course_repo.is_student_enrolled(current_user_id, course_id)
                if not is_enrolled:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Forbidden: Course is archived. Historical access is restricted to enrolled students.",
                    )
            elif (
                current_user_role
                and current_user_role.lower() == "instructor"
                and course.instructor_id != current_user_id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: You do not own this archived course",
                )

        return self._to_course_response(course)

    def list_courses(
        self,
        instructor_id: int | None = None,
        include_archived: bool = False,
    ) -> CourseListResponse:
        """List courses, optionally filtered by instructor or archive status."""
        courses = self.course_repo.list_courses(
            instructor_id=instructor_id,
            include_archived=include_archived,
        )
        return CourseListResponse(
            courses=[self._to_course_response(c) for c in courses],
            total=len(courses),
        )

    def update_course(
        self,
        course_id: int,
        payload: CourseUpdate,
        current_user_id: int,
        current_user_role: str,
    ) -> CourseResponse:
        """Update mutable course properties. Only owner instructor can modify."""
        course = self._verify_course_ownership(course_id, current_user_id, current_user_role)

        # Disallow content editing on archived courses (Decision D3)
        if course.is_archived and (payload.title is not None or payload.description is not None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit title or description of an archived course. Unarchive first.",
            )

        updated = self.course_repo.update_course(
            course_id=course_id,
            title=payload.title,
            description=payload.description,
            is_archived=payload.is_archived,
        )
        return self._to_course_response(updated)

    def archive_course(
        self,
        course_id: int,
        current_user_id: int,
        current_user_role: str,
    ) -> CourseResponse:
        """Archive a course (Decision D3)."""
        self._verify_course_ownership(course_id, current_user_id, current_user_role)
        archived = self.course_repo.archive_course(course_id)
        return self._to_course_response(archived)

    def publish_course(
        self,
        course_id: int,
        current_user_id: int,
        current_user_role: str,
    ) -> CourseResponse:
        """Publish / unarchive a course."""
        self._verify_course_ownership(course_id, current_user_id, current_user_role)
        published = self.course_repo.publish_course(course_id)
        return self._to_course_response(published)

    # =========================================================================
    # Topic Operations (FR-06, FR-07, FR-08, FR-09, Decision D2)
    # =========================================================================

    def create_topic(
        self,
        course_id: int,
        payload: TopicCreate,
        current_user_id: int,
        current_user_role: str,
    ) -> TopicResponse:
        """Add a new topic to a course. Only owner instructor can add topics (FR-06)."""
        course = self._verify_course_ownership(course_id, current_user_id, current_user_role)

        if course.is_archived:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot add topics to an archived course",
            )

        topic = self.course_repo.create_topic(
            course_id=course_id,
            title=payload.title,
            description=payload.description,
            order_index=payload.order_index,
        )
        return self._to_topic_response(topic)

    def get_topic(self, topic_id: int) -> TopicResponse:
        """Retrieve topic details by ID."""
        topic = self.course_repo.get_topic_by_id(topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with ID {topic_id} not found",
            )
        return self._to_topic_response(topic)

    def list_course_topics(
        self,
        course_id: int,
        active_only: bool = False,
        current_user_id: int | None = None,
        current_user_role: str | None = None,
    ) -> TopicListResponse:
        """List all topics for a course ordered sequentially."""
        course = self.course_repo.get_course_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found",
            )

        # Check archived access
        if (
            course.is_archived
            and current_user_id is not None
            and current_user_role
            and current_user_role.lower() == "student"
            and not self.course_repo.is_student_enrolled(current_user_id, course_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Course is archived. Topic access is restricted to enrolled students.",
            )

        topics = self.course_repo.list_course_topics(course_id, active_only=active_only)
        return TopicListResponse(
            course_id=course_id,
            topics=[self._to_topic_response(t) for t in topics],
            total=len(topics),
        )

    def update_topic(
        self,
        topic_id: int,
        payload: TopicUpdate,
        current_user_id: int,
        current_user_role: str,
    ) -> TopicResponse:
        """Update topic details. Only owner instructor can modify."""
        topic = self.course_repo.get_topic_by_id(topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with ID {topic_id} not found",
            )

        course = self._verify_course_ownership(topic.course_id, current_user_id, current_user_role)
        if course.is_archived:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify topics in an archived course",
            )

        updated = self.course_repo.update_topic(
            topic_id=topic_id,
            title=payload.title,
            description=payload.description,
            order_index=payload.order_index,
            is_active=payload.is_active,
        )
        return self._to_topic_response(updated)

    def delete_topic(
        self,
        topic_id: int,
        current_user_id: int,
        current_user_role: str,
    ) -> dict[str, str]:
        """Delete a topic, enforcing Decision D2 (reject if referenced by quiz questions)."""
        topic = self.course_repo.get_topic_by_id(topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic with ID {topic_id} not found",
            )

        course = self._verify_course_ownership(topic.course_id, current_user_id, current_user_role)
        if course.is_archived:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete topics from an archived course",
            )

        # Decision D2: Restrict topic deletion if quiz questions reference it
        if self.course_repo.has_quiz_questions(topic_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete topic referenced by existing quiz questions (Decision D2)",
            )

        self.course_repo.delete_topic(topic_id)
        return {"status": "success", "message": f"Topic {topic_id} deleted successfully"}

    def reorder_topics(
        self,
        course_id: int,
        payload: TopicReorderRequest,
        current_user_id: int,
        current_user_role: str,
    ) -> TopicListResponse:
        """Atomically update sequential order_index for course topics (FR-07)."""
        course = self._verify_course_ownership(course_id, current_user_id, current_user_role)
        if course.is_archived:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reorder topics in an archived course",
            )

        existing_topics = {t.id: t for t in self.course_repo.list_course_topics(course_id)}
        for item in payload.topics:
            if item.topic_id not in existing_topics:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Topic {item.topic_id} does not belong to course {course_id}",
                )

        topic_orders = [(item.topic_id, item.order_index) for item in payload.topics]
        updated = self.course_repo.reorder_topics(course_id, topic_orders)
        return TopicListResponse(
            course_id=course_id,
            topics=[self._to_topic_response(t) for t in updated],
            total=len(updated),
        )

    def add_prerequisite(
        self,
        topic_id: int,
        prerequisite_topic_id: int,
        current_user_id: int,
        current_user_role: str,
    ) -> TopicPrerequisiteResponse:
        """Add a directed prerequisite edge with validation for self, cross-course, and cycles."""
        topic = self.course_repo.get_topic_by_id(topic_id)
        prereq = self.course_repo.get_topic_by_id(prerequisite_topic_id)

        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target topic {topic_id} not found",
            )
        if not prereq:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prerequisite topic {prerequisite_topic_id} not found",
            )

        # Ownership check
        self._verify_course_ownership(topic.course_id, current_user_id, current_user_role)

        # Cross-course check
        if topic.course_id != prereq.course_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prerequisite topics must belong to the same course",
            )

        # Self-prerequisite check
        if topic_id == prerequisite_topic_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A topic cannot be a prerequisite of itself",
            )

        # Duplicate prerequisite edge check
        existing_prereqs = self.course_repo.get_prerequisites_for_topic(topic_id)
        if prerequisite_topic_id in existing_prereqs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Topic {prerequisite_topic_id} is already a prerequisite of topic {topic_id}",
            )

        try:
            edge = self.course_repo.add_prerequisite(topic_id, prerequisite_topic_id)
            return TopicPrerequisiteResponse(
                id=edge.id,
                topic_id=edge.topic_id,
                prerequisite_topic_id=edge.prerequisite_topic_id,
                created_at=edge.created_at,
            )
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Prerequisite relationship already exists",
            ) from e
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e

    def remove_prerequisite(
        self,
        topic_id: int,
        prerequisite_topic_id: int,
        current_user_id: int,
        current_user_role: str,
    ) -> dict[str, str]:
        """Remove a directed prerequisite edge."""
        topic = self.course_repo.get_topic_by_id(topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic {topic_id} not found",
            )

        self._verify_course_ownership(topic.course_id, current_user_id, current_user_role)
        removed = self.course_repo.remove_prerequisite(topic_id, prerequisite_topic_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prerequisite relationship between topic {topic_id} and {prerequisite_topic_id} does not exist",
            )
        return {"status": "success", "message": "Prerequisite relationship removed"}

    # =========================================================================
    # Enrollment Operations (FR-10, Decisions D6, D7)
    # =========================================================================

    def enroll_student(
        self,
        course_id: int,
        student_id: int,
        current_user_id: int,
        current_user_role: str,
        course_code: str | None = None,
    ) -> EnrollmentResponse:
        """Enroll a student in a course (FR-10, Decision D6)."""
        if current_user_role.lower() != "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Only students can enroll in courses",
            )

        # Privacy rule: Student cannot enroll another student
        if student_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Cannot enroll another student",
            )

        course = self.course_repo.get_course_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found",
            )

        # Decision D3: Archived courses disallow new enrollments
        if course.is_archived:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot enroll in an archived course",
            )

        # Course code verification if supplied
        if course_code is not None and course_code.strip().upper() != course.course_code.upper():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid course enrollment code: does not match course {course_id}",
            )

        # Duplicate enrollment check
        if self.course_repo.is_student_enrolled(student_id, course_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student {student_id} is already enrolled in course {course_id}",
            )

        enrollment = self.course_repo.enroll_student(student_id=student_id, course_id=course_id)
        return EnrollmentResponse(
            id=enrollment.id,
            student_id=enrollment.student_id,
            course_id=enrollment.course_id,
        )

    def get_student_enrollments(
        self,
        student_id: int,
        current_user_id: int,
        current_user_role: str,
    ) -> UserEnrollmentsResponse:
        """Retrieve all courses a student is enrolled in."""
        if current_user_role.lower() == "student" and student_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Cannot view another student's enrolled courses",
            )

        courses = self.course_repo.get_student_enrolled_courses(student_id)
        return UserEnrollmentsResponse(
            student_id=student_id,
            enrolled_courses=[self._to_course_response(c) for c in courses],
            total=len(courses),
        )

    def get_course_students(
        self,
        course_id: int,
        current_user_id: int,
        current_user_role: str,
    ) -> list[int]:
        """Retrieve student roster for a course. Only owner instructor can view."""
        self._verify_course_ownership(course_id, current_user_id, current_user_role)
        return self.course_repo.get_course_enrolled_students(course_id)

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    def _verify_course_ownership(
        self,
        course_id: int,
        user_id: int,
        user_role: str,
    ) -> CourseModel:
        """Verify that course exists and current user is the owner instructor."""
        if user_role.lower() != "instructor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Instructor role required",
            )

        course = self.course_repo.get_course_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found",
            )

        if course.instructor_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not own this course",
            )

        return course

    def _to_course_response(self, course: CourseModel) -> CourseResponse:
        """Convert CourseModel to Pydantic CourseResponse with aggregated metrics."""
        topics = self.course_repo.list_course_topics(course.id)
        students = self.course_repo.get_course_enrolled_students(course.id)
        return CourseResponse(
            id=course.id,
            title=course.title,
            description=course.description,
            course_code=course.course_code,
            instructor_id=course.instructor_id,
            is_archived=course.is_archived,
            created_at=course.created_at,
            updated_at=course.updated_at,
            topic_count=len(topics),
            enrollment_count=len(students),
        )

    def _to_topic_response(self, topic: TopicModel) -> TopicResponse:
        """Convert TopicModel to Pydantic TopicResponse with prerequisite IDs."""
        prereq_ids = self.course_repo.get_prerequisites_for_topic(topic.id)
        return TopicResponse(
            id=topic.id,
            course_id=topic.course_id,
            title=topic.title,
            description=topic.description,
            order_index=topic.order_index,
            is_active=topic.is_active,
            prerequisite_topic_ids=prereq_ids,
            created_at=topic.created_at,
            updated_at=topic.updated_at,
        )


# Global singleton instance for dependency injection
_global_course_service: CourseService | None = None


def get_course_service() -> CourseService:
    """Retrieve global CourseService singleton instance."""
    global _global_course_service
    if _global_course_service is None:
        _global_course_service = CourseService()
    return _global_course_service
