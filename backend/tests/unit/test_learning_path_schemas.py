"""Unit tests for Module 4: Personalized Learning Paths Pydantic schemas.

Requirements Traceability:
- FR-18: Learning path schema structure.
- FR-19: Recommendation rationale schema field.
- FR-20: Cold-start schema representation.
- FR-25: Defensive Pydantic v2 validation contracts with extra='forbid'.
"""

import pytest
from pydantic import ValidationError

from app.schemas.learning_path import LearningPathResponse, TopicPathItem


class TestTopicPathItemSchema:
    """Unit tests for TopicPathItem Pydantic schema."""

    def test_valid_topic_path_item(self):
        """Valid item instantiates correctly."""
        item = TopicPathItem(
            topic_id=1,
            title="Variables & Data Types",
            description="Foundational Python syntax",
            order_index=0,
            status="Proficient",
            score=0.92,
            is_unlocked=True,
            is_recommended=False,
            locked_reason=None,
            prerequisite_topic_ids=[],
            rationale=None,
        )
        assert item.topic_id == 1
        assert item.title == "Variables & Data Types"
        assert item.status == "Proficient"
        assert item.score == 0.92
        assert item.is_unlocked is True
        assert item.is_recommended is False
        assert item.locked_reason is None
        assert item.prerequisite_topic_ids == []

    def test_topic_path_item_with_recommendation_and_rationale(self):
        """Item with recommendation and rationale instantiates correctly."""
        item = TopicPathItem(
            topic_id=2,
            title="Control Flow",
            description=None,
            order_index=1,
            status="Weak",
            score=0.35,
            is_unlocked=True,
            is_recommended=True,
            locked_reason=None,
            prerequisite_topic_ids=[1],
            rationale="Topic is Weak (score: 0.35) and requires reinforcement.",
        )
        assert item.is_recommended is True
        assert item.rationale == "Topic is Weak (score: 0.35) and requires reinforcement."
        assert item.prerequisite_topic_ids == [1]

    def test_topic_path_item_locked_with_reason(self):
        """Locked item with locked_reason instantiates correctly."""
        item = TopicPathItem(
            topic_id=3,
            title="Functions & Scopes",
            description=None,
            order_index=2,
            status="Not Assessed",
            score=0.0,
            is_unlocked=False,
            is_recommended=False,
            locked_reason="Prerequisite 'Control Flow' not yet Proficient",
            prerequisite_topic_ids=[2],
            rationale=None,
        )
        assert item.is_unlocked is False
        assert "not yet Proficient" in item.locked_reason

    def test_score_boundary_validation_negative(self):
        """Score below 0.0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TopicPathItem(
                topic_id=1,
                title="Bad Score",
                order_index=0,
                status="Weak",
                score=-0.05,
                is_unlocked=True,
                is_recommended=False,
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_score_boundary_validation_exceeds_one(self):
        """Score above 1.0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            TopicPathItem(
                topic_id=1,
                title="Bad Score",
                order_index=0,
                status="Proficient",
                score=1.05,
                is_unlocked=True,
                is_recommended=False,
            )
        assert "less than or equal to 1" in str(exc_info.value)

    def test_extra_fields_forbidden_topic_item(self):
        """Extra unknown fields are rejected under extra='forbid'."""
        with pytest.raises(ValidationError) as exc_info:
            TopicPathItem(
                topic_id=1,
                title="Valid Topic",
                order_index=0,
                status="Proficient",
                score=0.9,
                is_unlocked=True,
                is_recommended=False,
                unexpected_field="injection_attempt",
            )
        assert "Extra inputs are not permitted" in str(exc_info.value)


class TestLearningPathResponseSchema:
    """Unit tests for LearningPathResponse Pydantic schema."""

    def test_valid_learning_path_response(self):
        """Valid full response instantiates correctly."""
        item = TopicPathItem(
            topic_id=1,
            title="Intro",
            order_index=0,
            status="Proficient",
            score=0.9,
            is_unlocked=True,
            is_recommended=False,
        )
        resp = LearningPathResponse(
            course_id=10,
            student_id=42,
            total_topics=1,
            unlocked_count=1,
            completed_count=1,
            completion_percentage=100.0,
            path=[item],
        )
        assert resp.course_id == 10
        assert resp.student_id == 42
        assert resp.total_topics == 1
        assert resp.unlocked_count == 1
        assert resp.completed_count == 1
        assert resp.completion_percentage == 100.0
        assert len(resp.path) == 1

    def test_empty_learning_path_response(self):
        """Empty path for zero-topic course instantiates correctly."""
        resp = LearningPathResponse(
            course_id=5,
            student_id=42,
            total_topics=0,
            unlocked_count=0,
            completed_count=0,
            completion_percentage=0.0,
            path=[],
        )
        assert resp.total_topics == 0
        assert resp.path == []

    def test_completion_percentage_below_zero_rejected(self):
        """Completion percentage < 0.0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            LearningPathResponse(
                course_id=1,
                student_id=1,
                total_topics=0,
                unlocked_count=0,
                completed_count=0,
                completion_percentage=-5.0,
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_completion_percentage_above_100_rejected(self):
        """Completion percentage > 100.0 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            LearningPathResponse(
                course_id=1,
                student_id=1,
                total_topics=1,
                unlocked_count=1,
                completed_count=1,
                completion_percentage=105.0,
            )
        assert "less than or equal to 100" in str(exc_info.value)

    def test_extra_fields_forbidden_learning_path_response(self):
        """Extra fields on LearningPathResponse are rejected under extra='forbid'."""
        with pytest.raises(ValidationError) as exc_info:
            LearningPathResponse(
                course_id=1,
                student_id=1,
                total_topics=0,
                unlocked_count=0,
                completed_count=0,
                completion_percentage=0.0,
                malicious_field="bad_payload",
            )
        assert "Extra inputs are not permitted" in str(exc_info.value)
