from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app

client = TestClient(app)


def test_seed_loss_records_returns_ranking() -> None:
    response = client.post(
        "/losses/seed",
        json={"reference_month": "2026-05"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["reference_month"] == "2026-05"
    assert data["total_records"] >= 3
    assert len(data["records"]) >= 3
    assert data["records"][0]["priority_score"] >= data["records"][-1]["priority_score"]


def test_loss_ranking_returns_records() -> None:
    client.post(
        "/losses/seed",
        json={"reference_month": "2026-05"},
    )

    response = client.get("/losses/ranking?reference_month=2026-05&limit=2")

    assert response.status_code == 200

    data = response.json()

    assert data["reference_month"] == "2026-05"
    assert data["total_records"] >= 3
    assert len(data["records"]) == 2


def test_loss_summary_returns_dashboard_metrics() -> None:
    client.post(
        "/losses/seed",
        json={"reference_month": "2026-05"},
    )

    response = client.get("/losses/summary?reference_month=2026-05")

    assert response.status_code == 200

    data = response.json()

    assert data["reference_month"] == "2026-05"
    assert data["total_areas"] >= 3
    assert data["estimated_loss_kwh"] > 0
    assert data["top_priority_score"] > 0
