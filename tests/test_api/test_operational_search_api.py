from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app

client = TestClient(app)


def test_operational_search_by_customer_endpoint_returns_response() -> None:
    response = client.get(
        "/operational/search/customer/UC-001",
        params={"reference_month": "2026-05"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["search_type"] == "customer"
    assert data["query"] == "UC-001"
    assert "asset" in data
    assert "customer_link" in data


def test_operational_search_by_transformer_endpoint_returns_response() -> None:
    response = client.get("/operational/search/transformer/TR-001")

    assert response.status_code == 200

    data = response.json()

    assert data["search_type"] == "transformer"
    assert data["query"] == "TR-001"
    assert "asset" in data


def test_operational_search_by_feeder_endpoint_returns_response() -> None:
    response = client.get("/operational/search/feeder/AL-01")

    assert response.status_code == 200

    data = response.json()

    assert data["search_type"] == "feeder"
    assert data["query"] == "AL-01"
    assert "total_records" in data
    assert "records" in data


def test_operational_search_by_substation_endpoint_returns_response() -> None:
    response = client.get("/operational/search/substation/SE-01")

    assert response.status_code == 200

    data = response.json()

    assert data["search_type"] == "substation"
    assert data["query"] == "SE-01"
    assert "total_records" in data
    assert "records" in data


def test_operational_search_by_coordinates_endpoint_returns_response() -> None:
    response = client.get(
        "/operational/search/coordinates",
        params={
            "latitude": -7.9401,
            "longitude": -34.8734,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["search_type"] == "coordinates"
    assert data["query"] == "-7.9401,-34.8734"
    assert "asset" in data
    assert "distance_meters" in data
