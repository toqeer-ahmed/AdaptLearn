"""Mastery calculation domain component (AdaptLearn M3).

Engine Isolation (NFR-05):
This module is part of the pure computational adaptive learning engine.
It must NOT import FastAPI, SQLAlchemy, Pydantic, or any database/web framework.

Requirements Traceability:
- FR-16: Recalculate student topic mastery score as the difficulty-weighted proportion
         of correct answers among the student's most recent N responses in that topic.
- TC-16-1: Latest 4 responses: Easy correct, Medium correct, Hard incorrect,
           Medium incorrect -> Score 0.375, level Weak.
- TC-16-2: Twelve stored responses with N = 10 -> only the latest 10 responses used.
- TC-16-4: Response record stores difficulty at time of attempt (historical capture).
- TC-17-2: Minimum response requirement (< min_responses -> Not Assessed).
- FR-20: Configurable parameters (weights, window size N, thresholds).
- NFR-05: Pure Python engine isolation.
- NFR-10: Deterministic calculations.
"""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from app.engine.mastery_policy import MasteryPolicy

DEFAULT_WEIGHTS: dict[str, float] = {
    "Easy": 1.0,
    "Medium": 2.0,
    "Hard": 3.0,
}

DEFAULT_WINDOW_SIZE: int = 10
VALID_DIFFICULTIES: frozenset[str] = frozenset({"Easy", "Medium", "Hard"})


@dataclass(frozen=True)
class ResponseRecord:
    """Historical record of a student's response to an assessment question.

    Per TC-16-4, the difficulty recorded at attempt time remains immutable,
    even if question bank attributes change later.

    Attributes:
        is_correct: Whether the student answered the question correctly.
        difficulty: Difficulty level at attempt time ('Easy', 'Medium', 'Hard').
        topic_id: Optional topic identifier for multi-topic grouping.
        attempt_id: Optional attempt identifier for traceability.
    """
    is_correct: bool
    difficulty: str
    topic_id: int | None = None
    attempt_id: int | None = None

    def __post_init__(self) -> None:
        """Validate and canonicalize difficulty to Title Case."""
        normalized = self.difficulty.strip().capitalize()
        if normalized not in VALID_DIFFICULTIES:
            raise ValueError(
                f"Invalid difficulty: '{self.difficulty}'. "
                f"Must be one of {sorted(VALID_DIFFICULTIES)}"
            )
        object.__setattr__(self, "difficulty", normalized)


@dataclass(frozen=True)
class MasteryParameters:
    """Configurable parameters governing mastery calculation and classification.

    Allows course-specific overrides per FR-20 and initial defaults from M1 A-06.

    Attributes:
        window_size: Maximum recent responses to include in calculation (N).
        easy_weight: Difficulty weight multiplier for Easy questions.
        medium_weight: Difficulty weight multiplier for Medium questions.
        hard_weight: Difficulty weight multiplier for Hard questions.
        weak_threshold: Upper exclusive bound for 'Weak' level.
        proficient_threshold: Lower inclusive bound for 'Proficient' level.
        min_responses: Minimum response count needed to evaluate score.
    """
    window_size: int = DEFAULT_WINDOW_SIZE
    easy_weight: float = 1.0
    medium_weight: float = 2.0
    hard_weight: float = 3.0
    weak_threshold: float = 0.50
    proficient_threshold: float = 0.80
    min_responses: int = 3


@dataclass(frozen=True)
class TopicMasteryResult:
    """Outcome of topic mastery recalculation.

    Attributes:
        score: Difficulty-weighted proportion of correct answers in [0.0, 1.0].
        level: Categorical mastery classification ('Not Assessed', 'Weak', 'Developing', 'Proficient').
        response_count: Total responses available for this topic.
        evaluated_responses: Number of responses included within the window N.
    """
    score: float
    level: str
    response_count: int
    evaluated_responses: int


class MasteryCalculator:
    """Calculates student topic mastery from historical response records.

    Strictly satisfies FR-16, TC-16-1, TC-16-2, TC-16-4, TC-17-2, and NFR-10.
    """

    def __init__(
        self,
        window_size: int = DEFAULT_WINDOW_SIZE,
        weights: Mapping[str, float] | None = None,
        policy: MasteryPolicy | None = None,
    ) -> None:
        """Initialize calculator with configurable window size, weights, and policy.

        Args:
            window_size: Number of recent responses to consider (must be >= 1).
            weights: Mapping of difficulty name to positive float weight.
            policy: MasteryPolicy instance for score classification.

        Raises:
            ValueError: If window_size < 1 or any weight is non-positive or missing.
        """
        if window_size < 1:
            raise ValueError(f"window_size must be at least 1, got {window_size}")
        self.window_size = window_size

        raw_weights = weights if weights is not None else DEFAULT_WEIGHTS
        validated_weights: dict[str, float] = {}
        for diff in ("Easy", "Medium", "Hard"):
            val = raw_weights.get(diff)
            if val is None:
                val = raw_weights.get(diff.lower())
            if val is None:
                raise ValueError(f"Missing required difficulty weight for '{diff}'")
            if val <= 0.0:
                raise ValueError(f"Weight for '{diff}' must be positive, got {val}")
            validated_weights[diff] = float(val)

        self.weights = validated_weights
        self.policy = policy or MasteryPolicy()

    @classmethod
    def from_parameters(cls, params: MasteryParameters) -> "MasteryCalculator":
        """Factory method to construct MasteryCalculator from a MasteryParameters object."""
        weights = {
            "Easy": params.easy_weight,
            "Medium": params.medium_weight,
            "Hard": params.hard_weight,
        }
        policy = MasteryPolicy(
            weak_threshold=params.weak_threshold,
            proficient_threshold=params.proficient_threshold,
            min_responses=params.min_responses,
        )
        return cls(
            window_size=params.window_size,
            weights=weights,
            policy=policy,
        )

    def calculate_score(
        self,
        responses: Sequence[ResponseRecord],
        window_size: int | None = None,
        weights: Mapping[str, float] | None = None,
    ) -> float:
        """Calculate the difficulty-weighted proportion of correct answers among recent responses.

        The formula is:
            Score = (sum of weights for correct responses in window) /
                    (sum of weights for all responses in window)

        Responses are evaluated in chronological order; the most recent N responses
        (slice responses[-N:]) are used per FR-16 and TC-16-2.

        Args:
            responses: Chronological sequence of student responses (oldest first, newest last).
            window_size: Optional override for window size N.
            weights: Optional override for difficulty weights.

        Returns:
            Calculated score in the range [0.0, 1.0]. Returns 0.0 if responses is empty.
        """
        if not responses:
            return 0.0

        n = window_size if window_size is not None else self.window_size
        if n < 1:
            raise ValueError(f"window_size must be at least 1, got {n}")

        active_weights = weights if weights is not None else self.weights
        window_responses = responses[-n:]

        total_weight = 0.0
        earned_weight = 0.0

        for record in window_responses:
            w = active_weights[record.difficulty]
            total_weight += w
            if record.is_correct:
                earned_weight += w

        if total_weight <= 0.0:
            return 0.0

        return earned_weight / total_weight

    def calculate_mastery(
        self,
        responses: Sequence[ResponseRecord],
        window_size: int | None = None,
        weights: Mapping[str, float] | None = None,
        policy: MasteryPolicy | None = None,
    ) -> TopicMasteryResult:
        """Calculate score and classify discrete mastery level.

        Evaluates the score across the window N and classifies the level
        via MasteryPolicy. If total responses < policy.min_responses,
        the level is 'Not Assessed' per FR-17 and TC-17-2.

        Args:
            responses: Chronological sequence of student responses for a single topic.
            window_size: Optional override for window size N.
            weights: Optional override for difficulty weights.
            policy: Optional override for MasteryPolicy.

        Returns:
            TopicMasteryResult containing score, level, response_count, and evaluated_responses.
        """
        active_policy = policy or self.policy
        total_count = len(responses)

        n = window_size if window_size is not None else self.window_size
        evaluated_count = min(total_count, n)

        score = self.calculate_score(responses, window_size=n, weights=weights)
        level = active_policy.classify(score, response_count=total_count)

        return TopicMasteryResult(
            score=score,
            level=level,
            response_count=total_count,
            evaluated_responses=evaluated_count,
        )

