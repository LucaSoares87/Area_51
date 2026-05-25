from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app

client = TestClient(app)


def test_transformer_loss_ranking_endpoint_returns_response() -> None:
    response = client.get(
        "/grid/transformers/ranking",
        params={
            "reference_month": "2026-05",
            "limit": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["reference_month"] == "2026-05"
    assert "total_records" in data
    assert "records" in data


def test_feeder_loss_ranking_endpoint_returns_response() -> None:
    response = client.get(
        "/grid/feeders/ranking",
        params={
            "reference_month": "2026-05",
            "limit": 10,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["reference_month"] == "2026-05"
    assert "total_records" in data
    assert "records" in data
