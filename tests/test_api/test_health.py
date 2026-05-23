from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app


def test_health_check_returns_healthy_status() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["service"] == "aerial_housing_detection"
    assert response.json()["version"] == "0.1.0"
