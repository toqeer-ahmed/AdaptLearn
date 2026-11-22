"""Unit tests for Module 1 Pydantic schemas and validation rules.

Requirements Traceability:
- FR-04: Course creation schema validation, uppercase course code format.
- FR-05: Course update and archiving schemas.
- FR-06: Topic creation schemas with sequential ordering bounds.
- FR-07: Batch topic reordering validation (no duplicate IDs or indices).
- FR-08: Topic prerequisite schemas with ID bounds.
- FR-10: Student enrollment request and response schemas.
- Decisions: D1 (course code bounds and regex), D3 (archiving flag), D6 (enrollment response).
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.course import (
    CourseCreate,
    CourseListResponse,
    CourseResponse,
    CourseUpdate,
    EnrollmentRequest,
    EnrollmentResponse,
    TopicCreate,
    TopicPrerequisiteCreate,
    TopicPrerequisiteResponse,
    TopicReorderItem,
    TopicReorderRequest,
    TopicResponse,
    TopicUpdate,
    UserEnrollmentsResponse,
)


class TestCourseSchemas:
    """Validate CourseCreate, CourseUpdate, and CourseResponse schemas."""

    def test_course_create_valid(self):
        """Valid course creation payload with code uppercase normalization."""
        schema = CourseCreate(
            title="Software Architecture",
            description="Comprehensive design patterns.",
            course_code="cs-arch-101",
        )
        assert schema.title == "Software Architecture"
        assert schema.description == "Comprehensive design patterns."
        # Auto-uppercase normalization per Decision D1
        assert schema.course_code == "CS-ARCH-101"

    def test_course_create_description_optional(self):
        """Course description is optional and defaults to None."""
        schema = CourseCreate(title="Algorithms", course_code="CS-201")
        assert schema.description is None
        assert schema.course_code == "CS-201"

    def test_course_create_missing_required_fields(self):
        """Missing title or course_code raises ValidationError."""
        with pytest.raises(ValidationError) as exc:
            CourseCreate()
        errors = exc.value.errors()
        field_names = [e["loc"][0] for e in errors]
        assert "title" in field_names
        assert "course_code" in field_names

    def test_course_create_empty_or_whitespace_title(self):
        """Empty or whitespace-only title raises ValidationError."""
        with pytest.raises(ValidationError):
            CourseCreate(title="   ", course_code="CS-101")

    @pytest.mark.parametrize(
        "invalid_code",
        [
            "c",  # Too short (< 3 chars)
            "c" * 51,  # Too long (> 50 chars)
            "CS 101",  # Contains spaces
            "CS@101!",  # Contains special characters
            "   ",  # Whitespace only
        ],
    )
    def test_course_create_invalid_code_format(self, invalid_code: str):
        """Invalid course code formats are rejected by regex and length constraints."""
        with pytest.raises(ValidationError):
            CourseCreate(title="Valid Title", course_code=invalid_code)

    def test_course_update_valid_partial(self):
        """Partial update supports individual fields."""
        u1 = CourseUpdate(title="New Title")
        assert u1.title == "New Title"
        assert u1.description is None
        assert u1.is_archived is None

        u2 = CourseUpdate(is_archived=True)
        assert u2.is_archived is True

    def test_course_update_empty_title_rejected(self):
        """If title is supplied in update, it cannot be empty or whitespace."""
        with pytest.raises(ValidationError):
            CourseUpdate(title="   ")

    def test_course_response_serialization(self):
        """CourseResponse correctly parses attributes and provides default counts."""
        now = datetime.now(timezone.utc)
        resp = CourseResponse(
            id=10,
            title="Database Systems",
            description="Relational calculus.",
            course_code="CS-DB-301",
            instructor_id=1,
            is_archived=False,
            created_at=now,
        )
        assert resp.id == 10
        assert resp.topic_count == 0
        assert resp.enrollment_count == 0
        assert resp.is_archived is False

    def test_course_list_response(self):
        """CourseListResponse aggregates course items with total count."""
        now = datetime.now(timezone.utc)
        c1 = CourseResponse(id=1, title="C1", course_code="C1", instructor_id=1, created_at=now)
        c2 = CourseResponse(id=2, title="C2", course_code="C2", instructor_id=1, created_at=now)
        list_resp = CourseListResponse(courses=[c1, c2], total=2)
        assert list_resp.total == 2
        assert len(list_resp.courses) == 2


class TestTopicSchemas:
    """Validate TopicCreate, TopicUpdate, TopicResponse, and TopicReorderRequest schemas."""

    def test_topic_create_valid(self):
        """Valid topic creation with explicit order_index."""
        topic = TopicCreate(title="Inheritance & Polymorphism", order_index=2)
        assert topic.title == "Inheritance & Polymorphism"
        assert topic.order_index == 2
        assert topic.description is None

    def test_topic_create_default_order(self):
        """Order index defaults to 0 if omitted."""
        topic = TopicCreate(title="Overview")
        assert topic.order_index == 0

    def test_topic_create_negative_order_rejected(self):
        """Negative order index is rejected by ge=0 validator."""
        with pytest.raises(ValidationError):
            TopicCreate(title="Invalid Topic", order_index=-1)

    def test_topic_create_empty_title_rejected(self):
        """Empty topic title is rejected."""
        with pytest.raises(ValidationError):
            TopicCreate(title="   ", order_index=0)

    def test_topic_update_valid(self):
        """Partial topic updates succeed."""
        u = TopicUpdate(is_active=False)
        assert u.is_active is False
        assert u.title is None

    def test_topic_reorder_request_valid(self):
        """Batch reordering request with unique IDs and unique indices succeeds."""
        req = TopicReorderRequest(
            topics=[
                TopicReorderItem(topic_id=1, order_index=0),
                TopicReorderItem(topic_id=2, order_index=1),
                TopicReorderItem(topic_id=3, order_index=2),
            ]
        )
        assert len(req.topics) == 3

    def test_topic_reorder_duplicate_topic_id_rejected(self):
        """Duplicate topic_id in reorder payload raises ValidationError."""
        with pytest.raises(ValidationError, match="Duplicate topic_id 1"):
            TopicReorderRequest(
                topics=[
                    TopicReorderItem(topic_id=1, order_index=0),
                    TopicReorderItem(topic_id=1, order_index=1),
                ]
            )

    def test_topic_reorder_duplicate_order_index_rejected(self):
        """Duplicate order_index in reorder payload raises ValidationError."""
        with pytest.raises(ValidationError, match="Duplicate order_index 0"):
            TopicReorderRequest(
                topics=[
                    TopicReorderItem(topic_id=1, order_index=0),
                    TopicReorderItem(topic_id=2, order_index=0),
                ]
            )

    def test_topic_reorder_empty_list_rejected(self):
        """Empty reordering list is rejected by min_length=1."""
        with pytest.raises(ValidationError):
            TopicReorderRequest(topics=[])

    def test_topic_response_defaults(self):
        """TopicResponse defaults prerequisite_topic_ids to empty list."""
        now = datetime.now(timezone.utc)
        resp = TopicResponse(
            id=5,
            course_id=1,
            title="Design Patterns",
            order_index=0,
            created_at=now,
        )
        assert resp.prerequisite_topic_ids == []
        assert resp.is_active is True


class TestPrerequisiteSchemas:
    """Validate TopicPrerequisiteCreate and TopicPrerequisiteResponse schemas."""

    def test_prerequisite_create_valid(self):
        """Valid prerequisite creation with positive integer identifier."""
        req = TopicPrerequisiteCreate(prerequisite_topic_id=3)
        assert req.prerequisite_topic_id == 3

    def test_prerequisite_create_non_positive_rejected(self):
        """Prerequisite ID <= 0 is rejected by ge=1 constraint."""
        with pytest.raises(ValidationError):
            TopicPrerequisiteCreate(prerequisite_topic_id=0)
        with pytest.raises(ValidationError):
            TopicPrerequisiteCreate(prerequisite_topic_id=-5)

    def test_prerequisite_response_serialization(self):
        """TopicPrerequisiteResponse serializes correctly."""
        now = datetime.now(timezone.utc)
        resp = TopicPrerequisiteResponse(
            id=1,
            topic_id=10,
            prerequisite_topic_id=5,
            created_at=now,
        )
        assert resp.id == 1
        assert resp.topic_id == 10
        assert resp.prerequisite_topic_id == 5


class TestEnrollmentSchemas:
    """Validate EnrollmentRequest and EnrollmentResponse schemas."""

    def test_enrollment_request_valid(self):
        """Valid course enrollment code is trimmed and uppercased."""
        req = EnrollmentRequest(course_code="  se-423-2026  ")
        assert req.course_code == "SE-423-2026"

    def test_enrollment_request_empty_rejected(self):
        """Empty course code raises ValidationError."""
        with pytest.raises(ValidationError):
            EnrollmentRequest(course_code="   ")

    def test_enrollment_response_serialization(self):
        """EnrollmentResponse serializes id, student_id, and course_id."""
        resp = EnrollmentResponse(id=1, student_id=2, course_id=10)
        assert resp.id == 1
        assert resp.student_id == 2
        assert resp.course_id == 10

    def test_user_enrollments_response(self):
        """UserEnrollmentsResponse wraps enrolled course list."""
        now = datetime.now(timezone.utc)
        course = CourseResponse(
            id=1, title="Test", course_code="TEST-1", instructor_id=1, created_at=now
        )
        resp = UserEnrollmentsResponse(student_id=2, enrolled_courses=[course], total=1)
        assert resp.student_id == 2
        assert resp.total == 1
        assert len(resp.enrolled_courses) == 1
