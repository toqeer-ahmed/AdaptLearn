"""Unit tests for the MasteryPolicy adaptive classification rules.

References:
- FR-17: Mastery score classification into Weak, Developing, or Proficient,
         reporting 'Not Assessed' when fewer than minimum responses exist.
- TC-17-1: Boundary test cases: 0.49 -> Weak, 0.50 -> Developing,
           0.79 -> Developing, 0.80 -> Proficient.
- TC-17-2: Minimum response requirement (default: 3) for 'Not Assessed'.
- Task E-01: Score bounds validation rejecting values outside [0.0, 1.0].
"""
import pytest

from app.engine.mastery_policy import (
    InvalidMasteryLevel,
    InvalidPolicyConfiguration,
    MasteryPolicy,
)


def test_classify_boundary_weak():
    """TC-17-1: Score 0.49 with default thresholds must classify as 'Weak'."""
    policy = MasteryPolicy()
    assert policy.classify(0.49) == "Weak"


def test_classify_boundary_developing_lower():
    """TC-17-1: Score 0.50 exactly at the weak threshold must classify as 'Developing'."""
    policy = MasteryPolicy()
    assert policy.classify(0.50) == "Developing"


def test_classify_boundary_developing_upper():
    """TC-17-1: Score 0.79 immediately below proficient threshold must classify as 'Developing'."""
    policy = MasteryPolicy()
    assert policy.classify(0.79) == "Developing"


def test_classify_boundary_proficient():
    """TC-17-1: Score 0.80 exactly at the proficient threshold must classify as 'Proficient'."""
    policy = MasteryPolicy()
    assert policy.classify(0.80) == "Proficient"


def test_classify_valid_bounds_zero_and_one():
    """Scores 0.0 and 1.0 are valid boundary values within the [0.0, 1.0] domain."""
    policy = MasteryPolicy()
    assert policy.classify(0.0) == "Weak"
    assert policy.classify(1.0) == "Proficient"


def test_classify_rejects_negative_score():
    """Score below 0.0 (-0.01) must raise InvalidMasteryLevel."""
    policy = MasteryPolicy()
    with pytest.raises(InvalidMasteryLevel):
        policy.classify(-0.01)


def test_classify_rejects_score_above_one():
    """Score above 1.0 (1.01) must raise InvalidMasteryLevel."""
    policy = MasteryPolicy()
    with pytest.raises(InvalidMasteryLevel):
        policy.classify(1.01)


def test_classify_not_assessed_under_minimum_responses():
    """TC-17-2: When response count is below minimum (default 3), level must be 'Not Assessed'."""
    policy = MasteryPolicy(min_responses=3)
    assert policy.classify(0.95, response_count=2) == "Not Assessed"
    assert policy.classify(0.20, response_count=2) == "Not Assessed"


def test_classify_assessed_at_minimum_responses():
    """TC-17-2: When response count meets minimum (3), level is determined by score."""
    policy = MasteryPolicy(min_responses=3)
    assert policy.classify(0.49, response_count=3) == "Weak"
    assert policy.classify(0.80, response_count=3) == "Proficient"


def test_classify_rejects_negative_response_count():
    """Negative response count is invalid and must raise ValueError."""
    policy = MasteryPolicy()
    with pytest.raises(ValueError):
        policy.classify(0.50, response_count=-1)


def test_policy_rejects_inverted_thresholds():
    """Weak threshold >= proficient threshold is invalid configuration."""
    with pytest.raises(InvalidPolicyConfiguration):
        MasteryPolicy(weak_threshold=0.85, proficient_threshold=0.70)


def test_policy_rejects_out_of_bound_thresholds():
    """Thresholds outside [0.0, 1.0] must raise InvalidPolicyConfiguration."""
    with pytest.raises(InvalidPolicyConfiguration):
        MasteryPolicy(weak_threshold=-0.1)
    with pytest.raises(InvalidPolicyConfiguration):
        MasteryPolicy(proficient_threshold=1.1)
