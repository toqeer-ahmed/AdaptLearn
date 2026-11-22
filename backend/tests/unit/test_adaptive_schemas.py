"""Unit tests for Adaptive Learning schemas and defense-in-depth validation (GAP-02).

Requirements Traceability:
- FR-16: Mastery score recalculation request schema and difficulty validation.
- GAP-02: Enforce accepted difficulty values ('Easy', 'Medium', 'Hard'),
          case-insensitivity, whitespace trimming, and prevention of unhandled 500s.
"""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.engine.mastery_calculator import MasteryParameters
from app.schemas.adaptive import (
    AttemptMasteryRecalculateRequest,
    AttemptResponseItem,
)
from app.services.adaptive_service import AdaptiveService


class TestAttemptResponseItemValidation:
    """Validate AttemptResponseItem schema difficulty validation and normalization."""

    @pytest.mark.parametrize(
        ("input_difficulty", "expected_normalized"),
        [
            ("Easy", "Easy"),
            ("Medium", "Medium"),
            ("Hard", "Hard"),
            ("easy", "Easy"),
            ("medium", "Medium"),
            ("hard", "Hard"),
            ("EASY", "Easy"),
            ("MEDIUM", "Medium"),
            ("HARD", "Hard"),
            ("eAsY", "Easy"),
            ("mEdIuM", "Medium"),
            ("hArD", "Hard"),
            ("  Easy  ", "Easy"),
            ("  medium\t", "Medium"),
            ("\nhard  ", "Hard"),
            ("  EASY  ", "Easy"),
        ],
    )
    def test_difficulty_valid_and_case_insensitive_normalized(
        self, input_difficulty: str, expected_normalized: str
    ):
        """Valid difficulty values in any casing and with surrounding whitespace are accepted and capitalized."""
        item = AttemptResponseItem(
            question_id=1,
            topic_id=10,
            difficulty=input_difficulty,
            is_correct=True,
        )
        assert item.difficulty == expected_normalized
        assert item.question_id == 1
        assert item.topic_id == 10
        assert item.is_correct is True

    @pytest.mark.parametrize(
        "invalid_difficulty",
        [
            "Expert",
            "Impossible",
            "Novice",
            "extreme",
            "",
            "   ",
            "\t\n",
            "unknown",
            "123",
            "Easy!",
        ],
    )
    def test_difficulty_invalid_values_raise_validation_error(
        self, invalid_difficulty: str
    ):
        """Invalid or unrecognized difficulty values raise Pydantic ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AttemptResponseItem(
                question_id=1,
                topic_id=10,
                difficulty=invalid_difficulty,
                is_correct=True,
            )
        errors = exc_info.value.errors()
        assert len(errors) >= 1
        assert errors[0]["loc"] == ("difficulty",)

    def test_attempt_recalculate_request_validates_nested_items(self):
        """AttemptMasteryRecalculateRequest rejects payloads containing invalid difficulty items."""
        valid_payload = {
            "student_id": 42,
            "course_id": 101,
            "responses": [
                {"question_id": 1, "topic_id": 1, "difficulty": "easy", "is_correct": True},
                {"question_id": 2, "topic_id": 1, "difficulty": "  Hard  ", "is_correct": False},
            ],
        }
        req = AttemptMasteryRecalculateRequest.model_validate(valid_payload)
        assert req.responses[0].difficulty == "Easy"
        assert req.responses[1].difficulty == "Hard"

        invalid_payload = {
            "student_id": 42,
            "course_id": 101,
            "responses": [
                {"question_id": 1, "topic_id": 1, "difficulty": "Easy", "is_correct": True},
                {"question_id": 2, "topic_id": 1, "difficulty": "SuperHard", "is_correct": False},
            ],
        }
        with pytest.raises(ValidationError) as exc_info:
            AttemptMasteryRecalculateRequest.model_validate(invalid_payload)
        assert any(err["loc"] == ("responses", 1, "difficulty") for err in exc_info.value.errors())


class TestAdaptiveServiceDefenseInDepth:
    """Validate AdaptiveService defense-in-depth for non-HTTP callers."""

    def test_service_prevalidation_prevents_partial_writes_on_invalid_difficulty(self):
        """If an invalid item reaches the service layer, it raises ValueError before any repository append."""
        mock_repo = MagicMock()
        mock_repo.get_course_settings.return_value = MasteryParameters()

        service = AdaptiveService(repository=mock_repo)

        # Create mock request where second item has an invalid difficulty (bypassing Pydantic)
        valid_item = MagicMock()
        valid_item.question_id = 1
        valid_item.topic_id = 10
        valid_item.difficulty = "Easy"
        valid_item.is_correct = True

        invalid_item = MagicMock()
        invalid_item.question_id = 2
        invalid_item.topic_id = 10
        invalid_item.difficulty = "Nightmare"
        invalid_item.is_correct = False

        request = MagicMock()
        request.course_id = 101
        request.student_id = 42
        request.responses = [valid_item, invalid_item]

        with pytest.raises(ValueError, match="Invalid difficulty: 'Nightmare'"):
            service.recalculate_attempt_mastery(request)

        # Verify that append_student_response was NEVER called (no partial writes!)
        mock_repo.append_student_response.assert_not_called()
