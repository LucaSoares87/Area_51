from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app

client = TestClient(app)


def test_operational_features_ranking_endpoint_returns_response() -> None:
    response = client.get("/features/operational/ranking?limit=10")

    assert response.status_code == 200

    payload = response.json()

    assert "total_records" in payload
    assert "records" in payload


def test_operational_features_transformer_endpoint_returns_response() -> None:
    response = client.get("/features/operational/transformer/A00074")

    assert response.status_code == 200

    payload = response.json()

    assert "found" in payload
    assert "records" in payload


def test_operational_features_export_endpoint_returns_csv() -> None:
    response = client.get("/features/operational/export.csv")

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "codigo_transformador" in response.text