"""Recommendation Strategy Domain System (AdaptLearn M3 / M4).

Engine Isolation (NFR-05):
This module is part of the pure computational adaptive learning engine.
It must NOT import FastAPI, SQLAlchemy, Pydantic, or any database/web framework.

Requirements Traceability:
- FR-18: Generate an ordered list of recommended topics: Weak topics before
         Developing topics, Proficient topics not recommended, and a topic whose
         prerequisites are not yet Proficient ranked after those prerequisites.
- FR-19: Display for each recommended topic its mastery score, level, and a short
         text stating the rule that caused the recommendation.
- TC-18-1: Weak topics listed before Developing topics.
- TC-18-2: Proficient topics are never recommended.
- TC-18-3: Prerequisite rule has priority over level ordering (A prereq of B -> A before B).
- TC-18-4: Deterministic ordering with alphabetical name tie-breaking (NFR-10).
- TC-18-5: Developing topics listed before Not Assessed topics.
- TC-18-6: All topics Proficient yields an empty recommendation list.
- Decision D1: Pure engine domain isolation.
"""
from abc import ABC, abstractmethod
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TopicRecommendationInput:
    """Input representation of a topic candidate for recommendation evaluation.

    Attributes:
        topic_id: Unique topic identifier.
        name: Name/title of the topic.
        mastery_level: Current mastery classification ('Weak', 'Developing', 'Proficient', 'Not Assessed').
        score: Numerical mastery score in [0.0, 1.0] (default: 0.0).
        prerequisites: Tuple of topic IDs that must be completed before this topic.
    """
    topic_id: int
    name: str
    mastery_level: str
    score: float = 0.0
    prerequisites: tuple[int, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TopicRecommendation:
    """An individual topic recommendation produced by a recommendation strategy.

    Attributes:
        topic_id: Recommended topic identifier.
        name: Name/title of the topic.
        mastery_level: Current mastery level.
        score: Current mastery score.
        rationale: Explanatory text stating the pedagogical rule for this recommendation (FR-19).
    """
    topic_id: int
    name: str
    mastery_level: str
    score: float
    rationale: str


class RecommendationStrategy(ABC):
    """Abstract Strategy interface for topic recommendation algorithms.

    Adheres to the Gang of Four Strategy Pattern: allows interchangeable recommendation
    algorithms to be defined and configured per course without modifying the engine.
    """

    @abstractmethod
    def recommend(
        self,
        topics: Sequence[TopicRecommendationInput],
        prerequisites: Mapping[int, Collection[int]] | None = None,
        max_recommendations: int | None = None,
    ) -> list[TopicRecommendation]:
        """Generate an ordered list of recommendations from candidate topics.

        Args:
            topics: Collection of topic inputs with mastery and prerequisite metadata.
            prerequisites: Optional mapping of topic_id -> set of prerequisite topic_ids.
                           If omitted, falls back to each topic's prerequisites attribute.
            max_recommendations: Optional upper bound on the number of returned recommendations.

        Returns:
            Ordered list of TopicRecommendation objects.
        """


class RuleBasedRecommendationStrategy(RecommendationStrategy):
    """Standard rule-based recommendation strategy adhering strictly to M1 Section 9.3.

    Selection Algorithm:
    1. Filter out all 'Proficient' topics (FR-18, TC-18-2).
    2. A candidate is available when every prerequisite that is also a candidate
       has already been placed in the recommendation list (TC-18-3).
    3. From available candidates, choose next topic by:
       - Level priority: Weak (0) -> Developing (1) -> Not Assessed (2)
       - Score: Lower score first (ascending)
       - Topic name: Alphabetical order (deterministic tie-breaking per TC-18-4)
       - Topic ID: Deterministic unique key tie-breaking
    4. Repeat until all non-Proficient candidates are placed or max_recommendations is reached.
    """

    # Categorical priority: lower integer means higher recommendation priority
    LEVEL_PRIORITY: Mapping[str, int] = {
        "Weak": 0,
        "Developing": 1,
        "Not Assessed": 2,
    }

    def recommend(
        self,
        topics: Sequence[TopicRecommendationInput],
        prerequisites: Mapping[int, Collection[int]] | None = None,
        max_recommendations: int | None = None,
    ) -> list[TopicRecommendation]:
        """Generate ordered recommendations following M1 Section 9.3."""
        if not topics:
            return []

        # Step 1: Filter out Proficient topics (FR-18, TC-18-2, TC-18-6)
        candidates: list[TopicRecommendationInput] = [
            t for t in topics if t.mastery_level != "Proficient"
        ]
        if not candidates:
            return []

        candidate_ids: set[int] = {t.topic_id for t in candidates}

        # Resolve prerequisite dependencies per topic
        effective_prereqs: dict[int, set[int]] = {}
        for t in candidates:
            if prerequisites is not None and t.topic_id in prerequisites:
                prereq_set = set(prerequisites[t.topic_id])
            else:
                prereq_set = set(t.prerequisites)
            # Only prerequisites that are unmastered candidates can block placement
            effective_prereqs[t.topic_id] = prereq_set.intersection(candidate_ids)

        placed: list[TopicRecommendation] = []
        placed_ids: set[int] = set()
        remaining = list(candidates)

        while remaining:
            # Step 2: Identify available candidates whose unmastered prerequisites are placed
            available = [
                t for t in remaining
                if effective_prereqs[t.topic_id].issubset(placed_ids)
            ]

            if not available:
                # Cycle or deadlock fallback: break tie among remaining topics
                available = remaining

            # Step 3: Choose next best topic by (level_priority, score, name, id)
            best_topic = min(
                available,
                key=lambda t: (
                    self.LEVEL_PRIORITY.get(t.mastery_level, 99),
                    t.score,
                    t.name.lower(),
                    t.topic_id,
                ),
            )

            # Generate explanatory rationale (FR-19)
            rationale = self._generate_rationale(best_topic, remaining, effective_prereqs)

            placed.append(
                TopicRecommendation(
                    topic_id=best_topic.topic_id,
                    name=best_topic.name,
                    mastery_level=best_topic.mastery_level,
                    score=best_topic.score,
                    rationale=rationale,
                )
            )
            placed_ids.add(best_topic.topic_id)
            remaining.remove(best_topic)

            if max_recommendations is not None and len(placed) >= max_recommendations:
                break

        return placed

    def _generate_rationale(
        self,
        topic: TopicRecommendationInput,
        remaining_candidates: Sequence[TopicRecommendationInput],
        effective_prereqs: Mapping[int, set[int]],
    ) -> str:
        """Create pedagogical rationale explaining why the topic was recommended (FR-19)."""
        # Check if another candidate explicitly depends on this topic
        is_blocking_dependency = any(
            topic.topic_id in effective_prereqs.get(other.topic_id, set())
            for other in remaining_candidates
            if other.topic_id != topic.topic_id
        )

        if topic.mastery_level == "Weak":
            return (
                f"Mastery score is Weak ({topic.score:.2f} < 0.50); "
                f"remediation and practice strongly recommended."
            )
        elif topic.mastery_level == "Developing":
            if is_blocking_dependency:
                return (
                    f"Mastery score is Developing ({topic.score:.2f}); "
                    f"required foundational prerequisite for subsequent topics."
                )
            return (
                f"Mastery score is Developing ({topic.score:.2f}); "
                f"practice recommended to attain proficiency."
            )
        elif topic.mastery_level == "Not Assessed":
            if is_blocking_dependency:
                return (
                    "Topic has not been assessed yet; "
                    "required prerequisite for subsequent topics."
                )
            return (
                "Topic has not been assessed yet; "
                "practice recommended to establish initial baseline mastery."
            )
        else:
            return f"Recommended topic based on mastery status ({topic.mastery_level})."


# ---------------------------------------------------------------------------
# Gang of Four (GoF) Factory Method Creational Pattern
# ---------------------------------------------------------------------------


class RecommendationStrategyCreator(ABC):
    """Abstract Creator in the Gang of Four (GoF) Factory Method pattern.

    Declares the factory method `create_strategy` that subclasses implement to
    instantiate specific `RecommendationStrategy` products. Subclasses override
    the factory method to alter the type of recommendation strategy created.

    Clients can invoke `recommend()` directly on the creator abstraction, which
    delegates execution to the product created by `create_strategy()`.
    """

    @abstractmethod
    def create_strategy(self) -> RecommendationStrategy:
        """Factory Method: instantiate and return a concrete RecommendationStrategy."""

    def recommend(
        self,
        topics: Sequence[TopicRecommendationInput],
        prerequisites: Mapping[int, Collection[int]] | None = None,
        max_recommendations: int | None = None,
    ) -> list[TopicRecommendation]:
        """Execute recommendation by creating and delegating to the strategy product.

        Template/operation method delegating to the factory-created product.
        """
        strategy = self.create_strategy()
        return strategy.recommend(
            topics=topics,
            prerequisites=prerequisites,
            max_recommendations=max_recommendations,
        )


class RuleBasedStrategyCreator(RecommendationStrategyCreator):
    """Concrete Creator implementing the Factory Method to produce RuleBasedRecommendationStrategy."""

    def create_strategy(self) -> RecommendationStrategy:
        """Instantiate and return the canonical RuleBasedRecommendationStrategy product."""
        return RuleBasedRecommendationStrategy()


# Strategy creator registry mapping identifier string to Creator class
STRATEGY_CREATORS: dict[str, type[RecommendationStrategyCreator]] = {
    "rule_based": RuleBasedStrategyCreator,
}

# Strategy registry mapping identifier string to Strategy class (backward compatibility)
RECOMMENDATION_STRATEGIES: dict[str, type[RecommendationStrategy]] = {
    "rule_based": RuleBasedRecommendationStrategy,
}


def get_strategy_creator(name: str = "rule_based") -> RecommendationStrategyCreator:
    """Resolve and instantiate a concrete strategy creator by name.

    Args:
        name: Identifier for the strategy creator (default: 'rule_based').

    Returns:
        Concrete RecommendationStrategyCreator instance.

    Raises:
        ValueError: If creator name is not registered.
    """
    creator_cls = STRATEGY_CREATORS.get(name.lower().strip())
    if creator_cls is None:
        raise ValueError(
            f"Unknown recommendation strategy creator: '{name}'. "
            f"Available creators: {sorted(STRATEGY_CREATORS.keys())}"
        )
    return creator_cls()


def get_recommendation_strategy(name: str = "rule_based") -> RecommendationStrategy:
    """Creational helper delegating object instantiation through the Factory Method pattern.

    Args:
        name: Registered strategy identifier (default: 'rule_based').

    Returns:
        Instantiated RecommendationStrategy produced by its corresponding Creator.

    Raises:
        ValueError: If strategy name is unrecognized.
    """
    creator = get_strategy_creator(name)
    return creator.create_strategy()


