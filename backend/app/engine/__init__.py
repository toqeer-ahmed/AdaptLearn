"""Adaptive Learning Engine Package (M3).

Engine Isolation (NFR-05):
This package and all submodules must remain pure Python.
Do NOT import FastAPI, SQLAlchemy, Pydantic, or any database/web framework.
"""
from app.engine.mastery_calculator import (
    DEFAULT_WEIGHTS,
    DEFAULT_WINDOW_SIZE,
    MasteryCalculator,
    MasteryParameters,
    ResponseRecord,
    TopicMasteryResult,
)
from app.engine.mastery_policy import (
    InvalidMasteryLevel,
    InvalidPolicyConfiguration,
    MasteryPolicy,
)
from app.engine.recommendation_strategy import (
    RECOMMENDATION_STRATEGIES,
    STRATEGY_CREATORS,
    RecommendationStrategy,
    RecommendationStrategyCreator,
    RuleBasedRecommendationStrategy,
    RuleBasedStrategyCreator,
    TopicRecommendation,
    TopicRecommendationInput,
    get_recommendation_strategy,
    get_strategy_creator,
)

__all__ = [
    "DEFAULT_WEIGHTS",
    "DEFAULT_WINDOW_SIZE",
    "RECOMMENDATION_STRATEGIES",
    "STRATEGY_CREATORS",
    "InvalidMasteryLevel",
    "InvalidPolicyConfiguration",
    "MasteryCalculator",
    "MasteryParameters",
    "MasteryPolicy",
    "RecommendationStrategy",
    "RecommendationStrategyCreator",
    "ResponseRecord",
    "RuleBasedRecommendationStrategy",
    "RuleBasedStrategyCreator",
    "TopicMasteryResult",
    "TopicRecommendation",
    "TopicRecommendationInput",
    "get_recommendation_strategy",
    "get_strategy_creator",
]
