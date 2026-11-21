"""Integration tests for Adaptive Learning Engine backend integration (AdaptLearn M3).

Requirements Traceability:
- FR-16: Recalculate mastery score after attempt submission.
- FR-17: Classify mastery level (Weak, Developing, Proficient, Not Assessed).
- FR-20: View and update adaptive parameters per course (GET/PUT /courses/{id}/adaptive-settings).
- FR-18 & FR-19: Get ordered recommendations with pedagogical rationales (GET /courses/{id}/recommendations).
- NFR-05 & NFR-15: Strict architectural layering (Router -> Service -> Repository -> Database; Service -> Engine).
"""
import pytest
from fastapi.testclient import TestClient

from app.engine.recommendation_strategy import TopicRecommendationInput
from app.main import app
from app.repositories.adaptive_repository import get_adaptive_repository


@pytest.fixture(autouse=True)
def reset_repository():
    """Reset repository in-memory state before each test for test isolation."""
    repo = get_adaptive_repository()
    repo.clear()
    yield repo
    repo.clear()


@pytest.fixture
def client():
    """FastAPI test client fixture."""
    return TestClient(app)


class TestAdaptiveSettingsEndpoints:
    """Validate GET and PUT /courses/{id}/adaptive-settings (FR-20, TC-20-1..TC-20-3)."""

    def test_get_default_adaptive_settings(self, client):
        """GET /courses/{id}/adaptive-settings returns M1 default baseline parameters."""
        response = client.get("/api/v1/courses/101/adaptive-settings")
        assert response.status_code == 200
        data = response.json()

        assert data["course_id"] == 101
        assert data["window_size"] == 10
        assert data["easy_weight"] == 1.0
        assert data["medium_weight"] == 2.0
        assert data["hard_weight"] == 3.0
        assert data["weak_threshold"] == 0.50
        assert data["proficient_threshold"] == 0.80
        assert data["min_responses"] == 3

    def test_update_adaptive_settings_fr_20(self, client):
        """PUT /courses/{id}/adaptive-settings updates course parameters successfully."""
        update_payload = {
            "window_size": 5,
            "medium_weight": 1.5,
            "hard_weight": 2.0,
        }
        response = client.put("/api/v1/courses/101/adaptive-settings", json=update_payload)
        assert response.status_code == 200
        data = response.json()

        assert data["course_id"] == 101
        assert data["window_size"] == 5
        assert data["medium_weight"] == 1.5
        assert data["hard_weight"] == 2.0
        # Untouched fields remain at defaults
        assert data["easy_weight"] == 1.0
        assert data["weak_threshold"] == 0.50

        # Verify persistence on subsequent GET
        get_res = client.get("/api/v1/courses/101/adaptive-settings")
        assert get_res.status_code == 200
        assert get_res.json()["window_size"] == 5
        assert get_res.json()["medium_weight"] == 1.5

    def test_update_adaptive_settings_rejects_inverted_thresholds(self, client):
        """PUT /courses/{id}/adaptive-settings rejects weak_threshold >= proficient_threshold."""
        invalid_payload = {
            "weak_threshold": 0.85,
            "proficient_threshold": 0.80,
        }
        response = client.put("/api/v1/courses/101/adaptive-settings", json=invalid_payload)
        assert response.status_code in (400, 422)

    def test_update_adaptive_settings_rejects_negative_window_size(self, client):
        """PUT /courses/{id}/adaptive-settings rejects window_size < 1."""
        invalid_payload = {"window_size": 0}
        response = client.put("/api/v1/courses/101/adaptive-settings", json=invalid_payload)
        assert response.status_code in (400, 422)


class TestRecommendationsEndpoint:
    """Validate GET /courses/{id}/recommendations (FR-18, FR-19, TC-18-1..TC-18-6)."""

    def test_get_recommendations_tc_18_3_scenario(self, client, reset_repository):
        """GET /courses/{id}/recommendations returns ordered topics per TC-18-3:
        Topic A (Developing, prereq of B), Topic B (Weak), Topic C (Weak, lowest score),
        Topic D (Proficient), Topic E (Not Assessed).
        Expected order: C, A, B, E; D is absent.
        """
        course_id = 200
        topics = [
            TopicRecommendationInput(topic_id=1, name="Topic A", mastery_level="Developing", score=0.60, prerequisites=()),
            TopicRecommendationInput(topic_id=2, name="Topic B", mastery_level="Weak", score=0.40, prerequisites=(1,)),
            TopicRecommendationInput(topic_id=3, name="Topic C", mastery_level="Weak", score=0.20, prerequisites=()),
            TopicRecommendationInput(topic_id=4, name="Topic D", mastery_level="Proficient", score=0.85, prerequisites=()),
            TopicRecommendationInput(topic_id=5, name="Topic E", mastery_level="Not Assessed", score=0.0, prerequisites=()),
        ]
        reset_repository.set_course_topics(course_id, topics)

        response = client.get(f"/api/v1/courses/{course_id}/recommendations")
        assert response.status_code == 200
        data = response.json()

        assert data["course_id"] == course_id
        recs = data["recommendations"]
        assert len(recs) == 4
        assert [r["topic_name"] for r in recs] == ["Topic C", "Topic A", "Topic B", "Topic E"]

        # Check rationales
        for r in recs:
            assert "rationale" in r
            assert len(r["rationale"]) > 0

    def test_get_recommendations_with_limit(self, client, reset_repository):
        """GET /courses/{id}/recommendations respects limit query parameter."""
        course_id = 201
        topics = [
            TopicRecommendationInput(topic_id=1, name="A", mastery_level="Weak", score=0.10),
            TopicRecommendationInput(topic_id=2, name="B", mastery_level="Weak", score=0.20),
            TopicRecommendationInput(topic_id=3, name="C", mastery_level="Weak", score=0.30),
        ]
        reset_repository.set_course_topics(course_id, topics)

        response = client.get(f"/api/v1/courses/{course_id}/recommendations?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) == 2
        assert [r["topic_name"] for r in data["recommendations"]] == ["A", "B"]


class TestRecalculateMasteryEndpoint:
    """Validate POST /courses/{id}/recalculate-mastery (FR-16, TC-16-1)."""

    def test_recalculate_mastery_tc_16_1(self, client):
        """POST /courses/{id}/recalculate-mastery recalculates mastery from attempt responses.
        TC-16-1: 4 responses (Easy correct, Medium correct, Hard incorrect, Medium incorrect)
        Expected: Score = 0.375, Level = 'Weak'.
        """
        payload = {
            "student_id": 42,
            "course_id": 300,
            "responses": [
                {"question_id": 1, "topic_id": 10, "difficulty": "Easy", "is_correct": True},
                {"question_id": 2, "topic_id": 10, "difficulty": "Medium", "is_correct": True},
                {"question_id": 3, "topic_id": 10, "difficulty": "Hard", "is_correct": False},
                {"question_id": 4, "topic_id": 10, "difficulty": "Medium", "is_correct": False},
            ],
        }
        response = client.post("/api/v1/courses/300/recalculate-mastery", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["student_id"] == 42
        assert data["course_id"] == 300
        updated = data["updated_topics"]
        assert len(updated) == 1
        topic_res = updated[0]
        assert topic_res["topic_id"] == 10
        assert pytest.approx(topic_res["score"], abs=1e-3) == 0.375
        assert topic_res["level"] == "Weak"
        assert topic_res["response_count"] == 4
