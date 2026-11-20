from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_health_check():
    """Verify that GET /health returns 200 OK and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "AdaptLearn"
    assert data["version"] == "0.1.0"


def test_v1_health_check():
    """Verify that GET /api/v1/health returns 200 OK and healthy status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "AdaptLearn"


def test_root_welcome():
    """Verify that GET / returns 200 OK with project metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "AdaptLearn"
    assert data["status"] == "operational"

