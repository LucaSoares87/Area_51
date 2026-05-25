from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app

client = TestClient(app)


def test_socioenergy_analysis_endpoint_returns_response() -> None:
    response = client.post(
        "/socioenergy/analysis",
        json={
            "reference_month": "2026-05",
            "estimated_roofs_by_area": [
                {
                    "area_id": "area-001",
                    "estimated_roofs": 145,
                }
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["reference_month"] == "2026-05"
    assert "total_records" in data
    assert "records" in data
