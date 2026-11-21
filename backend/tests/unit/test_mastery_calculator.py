"""Unit tests for the Mastery Calculator component (AdaptLearn M3).

Requirements Traceability:
- FR-16: Recalculate topic mastery score as the difficulty-weighted proportion
         of correct answers among the student's most recent N responses in that topic.
- TC-16-1: Latest 4 responses: Easy correct, Medium correct, Hard incorrect,
           Medium incorrect -> Score 0.375, level Weak.
- TC-16-2: Twelve stored responses with N = 10 -> only the latest 10 responses used.
           Also boundaries at exactly 10 and 11 responses.
- TC-16-4: Response record stores difficulty at time of attempt (historical capture).
- TC-17-2: Minimum response requirement (< min_responses -> Not Assessed).
- FR-20: Configurable parameters (weights, window size N, thresholds).
- NFR-05: Pure Python engine isolation (zero web/DB framework imports).
- NFR-10: Deterministic calculation.
"""
import ast
import math
from pathlib import Path

import pytest

from app.engine.mastery_calculator import (
    MasteryCalculator,
    MasteryParameters,
    ResponseRecord,
    TopicMasteryResult,
)
from app.engine.mastery_policy import MasteryPolicy


class TestTC161WorkedExample:
    """Validate the exact M1 baseline scenario from TC-16-1 and Section 9.2."""

    def test_tc_16_1_latest_four_responses_initial_parameters(self):
        """TC-16-1: Latest four responses in a topic:
        Easy correct, Medium correct, Hard incorrect, Medium incorrect (initial parameters).
        Expected: Score = 0.375, Level = 'Weak'.

        Math verification:
        Weights: Easy=1, Medium=2, Hard=3
        Earned: 1 + 2 + 0 + 0 = 3
        Total possible: 1 + 2 + 3 + 2 = 8
        Score: 3 / 8 = 0.375
        Level: 0.375 < 0.50 (weak_threshold) -> 'Weak'
        """
        responses = [
            ResponseRecord(is_correct=True, difficulty="Easy", topic_id=1),
            ResponseRecord(is_correct=True, difficulty="Medium", topic_id=1),
            ResponseRecord(is_correct=False, difficulty="Hard", topic_id=1),
            ResponseRecord(is_correct=False, difficulty="Medium", topic_id=1),
        ]

        calculator = MasteryCalculator()
        score = calculator.calculate_score(responses)
        assert math.isclose(score, 0.375, abs_tol=1e-6)

        result = calculator.calculate_mastery(responses)
        assert isinstance(result, TopicMasteryResult)
        assert math.isclose(result.score, 0.375, abs_tol=1e-6)
        assert result.level == "Weak"
        assert result.response_count == 4
        assert result.evaluated_responses == 4


class TestTC162WindowSlicing:
    """Validate the sliding window behavior for N most recent responses (TC-16-2)."""

    def test_tc_16_2_twelve_responses_with_window_ten(self):
        """TC-16-2: Twelve stored responses with N = 10.
        Only the latest 10 responses must be used.
        """
        # First 2 responses: Hard, correct (weight 3, earned 3)
        # Next 10 responses: Medium, incorrect (weight 2, earned 0)
        # If all 12 were used: score = 6 / (6 + 20) = 0.2307
        # With latest 10: all are Medium incorrect, score = 0 / 20 = 0.0
        responses = [
            ResponseRecord(is_correct=True, difficulty="Hard", topic_id=1),
            ResponseRecord(is_correct=True, difficulty="Hard", topic_id=1),
        ] + [
            ResponseRecord(is_correct=False, difficulty="Medium", topic_id=1)
            for _ in range(10)
        ]

        calculator = MasteryCalculator(window_size=10)
        score = calculator.calculate_score(responses)
        assert score == 0.0

        result = calculator.calculate_mastery(responses)
        assert result.score == 0.0
        assert result.level == "Weak"
        assert result.response_count == 12
        assert result.evaluated_responses == 10

    def test_tc_16_2_boundary_exactly_ten_responses(self):
        """Exactly 10 responses with N = 10 -> all 10 used."""
        responses = [
            ResponseRecord(is_correct=True, difficulty="Easy", topic_id=1)
            for _ in range(10)
        ]
        calculator = MasteryCalculator(window_size=10)
        result = calculator.calculate_mastery(responses)
        assert result.score == 1.0
        assert result.level == "Proficient"
        assert result.response_count == 10
        assert result.evaluated_responses == 10

    def test_tc_16_2_boundary_exactly_eleven_responses(self):
        """Exactly 11 responses with N = 10 -> first discarded, latest 10 used."""
        # 1st response: Easy incorrect (w=1, e=0) -> should be discarded
        # 2nd-11th (10 responses): Easy correct (w=1, e=1) -> used
        responses = [
            ResponseRecord(is_correct=False, difficulty="Easy", topic_id=1)
        ] + [
            ResponseRecord(is_correct=True, difficulty="Easy", topic_id=1)
            for _ in range(10)
        ]
        calculator = MasteryCalculator(window_size=10)
        result = calculator.calculate_mastery(responses)
        assert result.score == 1.0
        assert result.level == "Proficient"
        assert result.response_count == 11
        assert result.evaluated_responses == 10


class TestTC164DifficultyCapture:
    """Validate that responses retain their recorded difficulty at attempt time (TC-16-4)."""

    def test_recorded_difficulty_used_in_recalculation(self):
        """Historical response difficulty remains immutable during recalculation."""
        response = ResponseRecord(is_correct=True, difficulty="Medium", topic_id=2)
        assert response.difficulty == "Medium"

        calculator = MasteryCalculator()
        score = calculator.calculate_score([response])
        # 1 Medium correct: earned=2, total=2 -> score=1.0
        assert score == 1.0


class TestTC172MinimumResponsesWithPolicy:
    """Validate interaction with MasteryPolicy minimum response threshold (TC-17-2)."""

    def test_fewer_than_min_responses_yields_not_assessed(self):
        """2 responses with min_responses=3 yields 'Not Assessed' despite 100% correct."""
        responses = [
            ResponseRecord(is_correct=True, difficulty="Easy", topic_id=1),
            ResponseRecord(is_correct=True, difficulty="Easy", topic_id=1),
        ]
        calculator = MasteryCalculator(policy=MasteryPolicy(min_responses=3))
        result = calculator.calculate_mastery(responses)
        assert result.score == 1.0
        assert result.level == "Not Assessed"
        assert result.response_count == 2

    def test_exactly_min_responses_is_classified(self):
        """3 responses with min_responses=3 is classified by score."""
        responses = [
            ResponseRecord(is_correct=True, difficulty="Easy", topic_id=1),
            ResponseRecord(is_correct=True, difficulty="Easy", topic_id=1),
            ResponseRecord(is_correct=True, difficulty="Easy", topic_id=1),
        ]
        calculator = MasteryCalculator(policy=MasteryPolicy(min_responses=3))
        result = calculator.calculate_mastery(responses)
        assert result.score == 1.0
        assert result.level == "Proficient"
        assert result.response_count == 3


class TestScoreEdgeCases:
    """Test boundary conditions including empty responses and perfect/zero scores."""

    def test_empty_responses_yields_zero_and_not_assessed(self):
        """No responses recorded -> score 0.0, level 'Not Assessed'."""
        calculator = MasteryCalculator()
        score = calculator.calculate_score([])
        assert score == 0.0

        result = calculator.calculate_mastery([])
        assert result.score == 0.0
        assert result.level == "Not Assessed"
        assert result.response_count == 0
        assert result.evaluated_responses == 0

    def test_all_correct_responses_yields_score_one(self):
        """All responses correct -> score 1.0, level 'Proficient'."""
        responses = [
            ResponseRecord(is_correct=True, difficulty="Easy"),
            ResponseRecord(is_correct=True, difficulty="Medium"),
            ResponseRecord(is_correct=True, difficulty="Hard"),
        ]
        calculator = MasteryCalculator()
        result = calculator.calculate_mastery(responses)
        assert result.score == 1.0
        assert result.level == "Proficient"

    def test_all_incorrect_responses_yields_score_zero(self):
        """All responses incorrect with >= min_responses -> score 0.0, level 'Weak'."""
        responses = [
            ResponseRecord(is_correct=False, difficulty="Easy"),
            ResponseRecord(is_correct=False, difficulty="Medium"),
            ResponseRecord(is_correct=False, difficulty="Hard"),
        ]
        calculator = MasteryCalculator()
        result = calculator.calculate_mastery(responses)
        assert result.score == 0.0
        assert result.level == "Weak"


class TestConfigurabilityAndValidation:
    """Validate configurable parameters (FR-20) and input validation."""

    def test_custom_parameters_via_mastery_parameters(self):
        """Course-specific custom parameters (e.g. weights: Easy=1.0, Medium=1.5, Hard=2.0, N=5)."""
        params = MasteryParameters(
            window_size=5,
            easy_weight=1.0,
            medium_weight=1.5,
            hard_weight=2.0,
            weak_threshold=0.50,
            proficient_threshold=0.80,
            min_responses=3,
        )
        calculator = MasteryCalculator.from_parameters(params)

        # 2 Medium correct (1.5 * 2 = 3.0), 1 Hard incorrect (0.0)
        # Total possible: 1.5 + 1.5 + 2.0 = 5.0
        # Score: 3.0 / 5.0 = 0.60 -> 'Developing'
        responses = [
            ResponseRecord(is_correct=True, difficulty="Medium"),
            ResponseRecord(is_correct=True, difficulty="Medium"),
            ResponseRecord(is_correct=False, difficulty="Hard"),
        ]
        result = calculator.calculate_mastery(responses)
        assert math.isclose(result.score, 0.60, abs_tol=1e-6)
        assert result.level == "Developing"

    def test_difficulty_case_insensitivity(self):
        """Difficulty strings with varied casing are normalized."""
        r1 = ResponseRecord(is_correct=True, difficulty="easy")
        r2 = ResponseRecord(is_correct=True, difficulty="MEDIUM")
        r3 = ResponseRecord(is_correct=True, difficulty="Hard")
        assert r1.difficulty == "Easy"
        assert r2.difficulty == "Medium"
        assert r3.difficulty == "Hard"

    def test_invalid_difficulty_raises_value_error(self):
        """Unrecognized difficulty level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid difficulty"):
            ResponseRecord(is_correct=True, difficulty="Expert")

    def test_invalid_window_size_raises_value_error(self):
        """Window size N < 1 raises ValueError."""
        with pytest.raises(ValueError, match="window_size must be at least 1"):
            MasteryCalculator(window_size=0)

    def test_invalid_weight_raises_value_error(self):
        """Non-positive difficulty weights raise ValueError."""
        with pytest.raises(ValueError, match="Weight for 'Easy' must be positive"):
            MasteryCalculator(weights={"Easy": 0.0, "Medium": 2.0, "Hard": 3.0})

        with pytest.raises(ValueError, match="Weight for 'Hard' must be positive"):
            MasteryCalculator(weights={"Easy": 1.0, "Medium": 2.0, "Hard": -1.0})


class TestEngineIsolation:
    """Verify architectural constraint NFR-05: Pure Python engine isolation."""

    def test_mastery_calculator_has_zero_framework_imports(self):
        """The mastery calculator module must not import FastAPI, SQLAlchemy, or Pydantic."""
        calculator_path = (
            Path(__file__).resolve().parent.parent.parent
            / "app"
            / "engine"
            / "mastery_calculator.py"
        )
        assert calculator_path.exists(), f"File {calculator_path} does not exist"

        tree = ast.parse(calculator_path.read_text(encoding="utf-8"))
        disallowed_prefixes = (
            "fastapi",
            "sqlalchemy",
            "pydantic",
            "starlette",
            "requests",
            "httpx",
            "app.domain",
            "app.repositories",
            "app.services",
            "app.api",
        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(disallowed_prefixes), (
                        f"Forbidden framework import in engine: {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(disallowed_prefixes), (
                    f"Forbidden framework import in engine: {node.module}"
                )
