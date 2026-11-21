"""Unit tests for the Recommendation Strategy System (AdaptLearn M3 / M4).

Requirements Traceability:
- FR-18: Generate an ordered list of recommended topics: Weak topics before
         Developing topics, Proficient topics not recommended, and a topic whose
         prerequisites are not yet Proficient ranked after those prerequisites.
- FR-19: Display for each recommended topic its mastery score, level, and a short
         text stating the rule that caused the recommendation.
- TC-18-1: One Weak and one Developing topic without prerequisites -> Weak listed first.
- TC-18-2: Topic at level Proficient -> Not recommended.
- TC-18-3: Prerequisite rule: A (Developing) is prereq of B (Weak), C (Weak, lower score than B),
           D (Proficient), E (Not Assessed). Order: C, A, B, E; D absent. B follows A.
- TC-18-4: Determinism: Two Weak topics with equal scores -> ordered by name alphabetically,
           identical on repeated calculations.
- TC-18-5: Not Assessed topics: Developing listed before Not Assessed.
- TC-18-6: All topics Proficient -> Empty recommendation list.
- NFR-05: Pure Python engine isolation.
- NFR-10: Deterministic calculations.
"""
from collections.abc import Sequence

import pytest

from app.engine.recommendation_strategy import (
    RecommendationStrategy,
    RecommendationStrategyCreator,
    RuleBasedRecommendationStrategy,
    RuleBasedStrategyCreator,
    TopicRecommendation,
    TopicRecommendationInput,
    get_recommendation_strategy,
    get_strategy_creator,
)


class TestTC18M1BaselineScenarios:
    """Validate all confirmed M1 baseline test cases from Section 9.3 and Section 16.2."""

    def test_tc_18_1_weak_before_developing(self):
        """TC-18-1: One Weak and one Developing topic without prerequisites -> Weak listed first."""
        topics = [
            TopicRecommendationInput(
                topic_id=1, name="Recursion", mastery_level="Developing", score=0.65
            ),
            TopicRecommendationInput(
                topic_id=2, name="Pointers", mastery_level="Weak", score=0.35
            ),
        ]
        strategy = RuleBasedRecommendationStrategy()
        recs = strategy.recommend(topics)

        assert len(recs) == 2
        assert recs[0].topic_id == 2
        assert recs[0].name == "Pointers"
        assert recs[0].mastery_level == "Weak"
        assert recs[1].topic_id == 1
        assert recs[1].name == "Recursion"
        assert recs[1].mastery_level == "Developing"

    def test_tc_18_2_proficient_topics_excluded(self):
        """TC-18-2: Proficient topics are never recommended."""
        topics = [
            TopicRecommendationInput(
                topic_id=10, name="Variables", mastery_level="Proficient", score=0.90
            ),
            TopicRecommendationInput(
                topic_id=11, name="Loops", mastery_level="Weak", score=0.30
            ),
        ]
        strategy = RuleBasedRecommendationStrategy()
        recs = strategy.recommend(topics)

        assert len(recs) == 1
        assert recs[0].topic_id == 11
        assert recs[0].name == "Loops"
        # Proficient topic 10 is absent
        assert all(r.topic_id != 10 for r in recs)

    def test_tc_18_3_prerequisite_rule_worked_example(self):
        """TC-18-3: Topic A is a prerequisite of B.
        A is Developing, B is Weak, C is Weak with a lower score than B,
        D is Proficient, and E is Not Assessed.
        Expected order: C, A, B, E; D is absent. B follows A although B is Weak.
        """
        topics = [
            TopicRecommendationInput(
                topic_id=1, name="Topic A", mastery_level="Developing", score=0.60, prerequisites=()
            ),
            TopicRecommendationInput(
                topic_id=2, name="Topic B", mastery_level="Weak", score=0.40, prerequisites=(1,)
            ),
            TopicRecommendationInput(
                topic_id=3, name="Topic C", mastery_level="Weak", score=0.20, prerequisites=()
            ),
            TopicRecommendationInput(
                topic_id=4, name="Topic D", mastery_level="Proficient", score=0.85, prerequisites=()
            ),
            TopicRecommendationInput(
                topic_id=5, name="Topic E", mastery_level="Not Assessed", score=0.0, prerequisites=()
            ),
        ]
        strategy = RuleBasedRecommendationStrategy()
        recs = strategy.recommend(topics)

        assert [r.name for r in recs] == ["Topic C", "Topic A", "Topic B", "Topic E"]
        assert all(r.name != "Topic D" for r in recs)

    def test_tc_18_4_determinism_and_name_tie_breaking(self):
        """TC-18-4: Two Weak topics with equal scores are ordered by name alphabetically,
        and repeated calculation yields identical output on every run (NFR-10).
        """
        topics = [
            TopicRecommendationInput(
                topic_id=1, name="Graphs", mastery_level="Weak", score=0.30
            ),
            TopicRecommendationInput(
                topic_id=2, name="Arrays", mastery_level="Weak", score=0.30
            ),
        ]
        strategy = RuleBasedRecommendationStrategy()

        # Run 5 consecutive times to prove deterministic repeatability
        for _ in range(5):
            recs = strategy.recommend(topics)
            assert [r.name for r in recs] == ["Arrays", "Graphs"]

    def test_tc_18_5_developing_before_not_assessed(self):
        """TC-18-5: A Not Assessed topic and a Developing topic -> Developing listed first."""
        topics = [
            TopicRecommendationInput(
                topic_id=1, name="Trees", mastery_level="Not Assessed", score=0.0
            ),
            TopicRecommendationInput(
                topic_id=2, name="Stacks", mastery_level="Developing", score=0.55
            ),
        ]
        strategy = RuleBasedRecommendationStrategy()
        recs = strategy.recommend(topics)

        assert [r.name for r in recs] == ["Stacks", "Trees"]

    def test_tc_18_6_all_proficient_yields_empty_list(self):
        """TC-18-6: When all course topics are Proficient, the recommendation list is empty."""
        topics = [
            TopicRecommendationInput(topic_id=1, name="T1", mastery_level="Proficient", score=0.85),
            TopicRecommendationInput(topic_id=2, name="T2", mastery_level="Proficient", score=0.92),
            TopicRecommendationInput(topic_id=3, name="T3", mastery_level="Proficient", score=1.0),
        ]
        strategy = RuleBasedRecommendationStrategy()
        recs = strategy.recommend(topics)

        assert recs == []


class TestPrerequisiteAndBoundaryEdgeCases:
    """Validate prerequisite resolution boundaries and edge cases."""

    def test_proficient_prerequisite_does_not_block_candidate(self):
        """If a prerequisite is already Proficient, it is not a candidate and does not block."""
        topics = [
            TopicRecommendationInput(
                topic_id=1, name="Basic Math", mastery_level="Proficient", score=0.95
            ),
            TopicRecommendationInput(
                topic_id=2, name="Calculus", mastery_level="Weak", score=0.25, prerequisites=(1,)
            ),
        ]
        strategy = RuleBasedRecommendationStrategy()
        recs = strategy.recommend(topics)

        assert len(recs) == 1
        assert recs[0].topic_id == 2
        assert recs[0].name == "Calculus"

    def test_external_prerequisites_map_override(self):
        """Prerequisites can be provided via a separate adjacency dictionary."""
        topics = [
            TopicRecommendationInput(topic_id=1, name="Topic 1", mastery_level="Developing", score=0.60),
            TopicRecommendationInput(topic_id=2, name="Topic 2", mastery_level="Weak", score=0.30),
        ]
        prereqs = {2: {1}}  # Topic 2 requires Topic 1
        strategy = RuleBasedRecommendationStrategy()
        recs = strategy.recommend(topics, prerequisites=prereqs)

        # Topic 1 must be recommended before Topic 2 because 1 is a prereq of 2
        assert [r.topic_id for r in recs] == [1, 2]

    def test_max_recommendations_limit(self):
        """max_recommendations truncates the list to the requested limit."""
        topics = [
            TopicRecommendationInput(topic_id=1, name="A", mastery_level="Weak", score=0.10),
            TopicRecommendationInput(topic_id=2, name="B", mastery_level="Weak", score=0.20),
            TopicRecommendationInput(topic_id=3, name="C", mastery_level="Weak", score=0.30),
        ]
        strategy = RuleBasedRecommendationStrategy()
        recs = strategy.recommend(topics, max_recommendations=2)

        assert len(recs) == 2
        assert [r.name for r in recs] == ["A", "B"]

    def test_recommendation_rationale_non_empty(self):
        """Every recommendation has an informative, non-empty rationale string (FR-19)."""
        topics = [
            TopicRecommendationInput(topic_id=1, name="A", mastery_level="Weak", score=0.20),
            TopicRecommendationInput(topic_id=2, name="B", mastery_level="Developing", score=0.60),
            TopicRecommendationInput(topic_id=3, name="C", mastery_level="Not Assessed", score=0.0),
        ]
        strategy = RuleBasedRecommendationStrategy()
        recs = strategy.recommend(topics)

        for rec in recs:
            assert isinstance(rec.rationale, str)
            assert len(rec.rationale.strip()) > 0
            assert rec.mastery_level in ("Weak", "Developing", "Not Assessed")


class TestStrategyPatternInterchangeability:
    """Validate that the recommendation strategy pattern is modular and extensible."""

    def test_custom_strategy_interchangeability(self):
        """A custom strategy implementing RecommendationStrategy can be substituted cleanly."""
        class MockTopWeakOnlyStrategy(RecommendationStrategy):
            def recommend(
                self,
                topics: Sequence[TopicRecommendationInput],
                prerequisites: dict | None = None,
                max_recommendations: int | None = None,
            ) -> list[TopicRecommendation]:
                # Only recommends Weak topics, ignoring all others
                weak_only = [
                    TopicRecommendation(
                        topic_id=t.topic_id,
                        name=t.name,
                        mastery_level=t.mastery_level,
                        score=t.score,
                        rationale="Remediation needed for weak topic",
                    )
                    for t in topics
                    if t.mastery_level == "Weak"
                ]
                return weak_only

        custom_strategy = MockTopWeakOnlyStrategy()
        topics = [
            TopicRecommendationInput(topic_id=1, name="A", mastery_level="Developing", score=0.6),
            TopicRecommendationInput(topic_id=2, name="B", mastery_level="Weak", score=0.3),
        ]
        recs = custom_strategy.recommend(topics)
        assert len(recs) == 1
        assert recs[0].topic_id == 2

    def test_get_recommendation_strategy_registry(self):
        """Strategy registry function resolves 'rule_based' and rejects unknown strategies."""
        strat = get_recommendation_strategy("rule_based")
        assert isinstance(strat, RuleBasedRecommendationStrategy)

        with pytest.raises(ValueError, match="Unknown recommendation strategy"):
            get_recommendation_strategy("non_existent_strategy")


class TestFactoryMethodPattern:
    """Validate GoF Factory Method pattern implementation (SE423 Rubric & DEF-ARCH-001)."""

    def test_creator_abstraction_cannot_be_instantiated(self):
        """RecommendationStrategyCreator is an abstract class and cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            RecommendationStrategyCreator()  # type: ignore[abstract]

    def test_rule_based_creator_returns_expected_strategy(self):
        """RuleBasedStrategyCreator.create_strategy() instantiates a RuleBasedRecommendationStrategy."""
        creator = RuleBasedStrategyCreator()
        strategy = creator.create_strategy()

        assert isinstance(strategy, RuleBasedRecommendationStrategy)
        assert isinstance(strategy, RecommendationStrategy)

    def test_creator_recommend_delegates_to_factory_method_product(self):
        """Creator's recommend() method delegates directly to the product created by create_strategy()."""
        creator = RuleBasedStrategyCreator()
        topics = [
            TopicRecommendationInput(topic_id=1, name="Recursion", mastery_level="Developing", score=0.65),
            TopicRecommendationInput(topic_id=2, name="Pointers", mastery_level="Weak", score=0.35),
        ]
        recs = creator.recommend(topics)

        assert len(recs) == 2
        assert recs[0].topic_id == 2
        assert recs[0].name == "Pointers"
        assert recs[1].topic_id == 1
        assert recs[1].name == "Recursion"

    def test_polymorphic_subclass_creator(self):
        """A new creator subclass can override create_strategy() without altering existing clients."""
        class MockTopWeakOnlyStrategy(RecommendationStrategy):
            def recommend(
                self,
                topics: Sequence[TopicRecommendationInput],
                prerequisites: dict | None = None,
                max_recommendations: int | None = None,
            ) -> list[TopicRecommendation]:
                return [
                    TopicRecommendation(
                        topic_id=t.topic_id,
                        name=t.name,
                        mastery_level=t.mastery_level,
                        score=t.score,
                        rationale="Remediation needed for weak topic",
                    )
                    for t in topics
                    if t.mastery_level == "Weak"
                ]

        class MockTopWeakCreator(RecommendationStrategyCreator):
            def create_strategy(self) -> RecommendationStrategy:
                return MockTopWeakOnlyStrategy()

        creator = MockTopWeakCreator()
        strategy = creator.create_strategy()
        assert isinstance(strategy, MockTopWeakOnlyStrategy)
        assert isinstance(strategy, RecommendationStrategy)

        topics = [
            TopicRecommendationInput(topic_id=1, name="A", mastery_level="Developing", score=0.6),
            TopicRecommendationInput(topic_id=2, name="B", mastery_level="Weak", score=0.3),
        ]
        recs = creator.recommend(topics)
        assert len(recs) == 1
        assert recs[0].topic_id == 2

    def test_get_strategy_creator_resolution(self):
        """get_strategy_creator resolves 'rule_based' and raises ValueError for unknown creators."""
        creator = get_strategy_creator("rule_based")
        assert isinstance(creator, RuleBasedStrategyCreator)
        assert isinstance(creator, RecommendationStrategyCreator)

        # Case-insensitive resolution
        creator_upper = get_strategy_creator("RULE_BASED")
        assert isinstance(creator_upper, RuleBasedStrategyCreator)

        with pytest.raises(ValueError, match="Unknown recommendation strategy creator"):
            get_strategy_creator("stale_first_unimplemented")

    def test_get_recommendation_strategy_delegates_through_creator(self):
        """get_recommendation_strategy helper delegates instantiation through the creator hierarchy."""
        strategy = get_recommendation_strategy("rule_based")
        assert isinstance(strategy, RuleBasedRecommendationStrategy)


