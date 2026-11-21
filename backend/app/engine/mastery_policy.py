"""Mastery policy domain model and classification rules.

Engine Isolation (NFR-05):
This module is part of the pure computational adaptive learning engine.
It must NOT import FastAPI, SQLAlchemy, Pydantic, or any database/web framework.

Requirements Traceability:
- FR-17: Classify mastery score as Weak, Developing, or Proficient;
         report Not Assessed when fewer than minimum responses exist.
- TC-17-1: Boundary values 0.49 (Weak), 0.50 (Developing),
           0.79 (Developing), 0.80 (Proficient).
- TC-17-2: Minimum response requirement (default: 3) for Not Assessed.
"""
from dataclasses import dataclass


class InvalidMasteryLevel(ValueError):
    """Raised when a mastery score falls outside the valid range [0.0, 1.0]."""


class InvalidPolicyConfiguration(ValueError):
    """Raised when threshold or response count configurations violate domain rules."""


@dataclass(frozen=True)
class MasteryPolicy:
    """Configurable domain policy governing mastery score classification.

    Attributes:
        weak_threshold: Upper exclusive bound for 'Weak' level (default: 0.50).
        proficient_threshold: Lower inclusive bound for 'Proficient' level (default: 0.80).
        min_responses: Minimum response count needed to evaluate score (default: 3).
    """
    weak_threshold: float = 0.50
    proficient_threshold: float = 0.80
    min_responses: int = 3

    def __post_init__(self) -> None:
        """Validate configuration parameters upon policy creation."""
        if not (0.0 <= self.weak_threshold <= 1.0):
            raise InvalidPolicyConfiguration(
                f"weak_threshold must be between 0.0 and 1.0, got {self.weak_threshold}"
            )
        if not (0.0 <= self.proficient_threshold <= 1.0):
            raise InvalidPolicyConfiguration(
                f"proficient_threshold must be between 0.0 and 1.0, got {self.proficient_threshold}"
            )
        if self.weak_threshold >= self.proficient_threshold:
            raise InvalidPolicyConfiguration(
                f"weak_threshold ({self.weak_threshold}) must be strictly less than "
                f"proficient_threshold ({self.proficient_threshold})"
            )
        if self.min_responses < 1:
            raise InvalidPolicyConfiguration(
                f"min_responses must be at least 1, got {self.min_responses}"
            )

    def classify(self, score: float, response_count: int | None = None) -> str:
        """Classify a mastery score into a discrete mastery level.

        Args:
            score: Student's mastery score in the inclusive range [0.0, 1.0].
            response_count: Optional count of recorded responses for the topic.
                            If provided and < min_responses, returns 'Not Assessed'.
                            If omitted, assumes response count condition is satisfied.

        Returns:
            One of the official M1 classification labels:
            'Not Assessed', 'Weak', 'Developing', 'Proficient'.

        Raises:
            InvalidMasteryLevel: If score is strictly outside [0.0, 1.0].
            ValueError: If response_count is negative.
        """
        if response_count is not None:
            if response_count < 0:
                raise ValueError(
                    f"response_count cannot be negative, got {response_count}"
                )
            if response_count < self.min_responses:
                return "Not Assessed"

        # Validate score bounds [0.0, 1.0]
        if score < 0.0 or score > 1.0:
            raise InvalidMasteryLevel(
                f"Mastery score must be in range [0.0, 1.0], got {score}"
            )

        # Classification based on confirmed M1 thresholds (FR-17, TC-17-1)
        if score < self.weak_threshold:
            return "Weak"
        elif score < self.proficient_threshold:
            return "Developing"
        else:
            return "Proficient"

