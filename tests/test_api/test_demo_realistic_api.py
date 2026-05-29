import subprocess
import sys

from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app

client = TestClient(app)


def test_realistic_analysis_endpoint_returns_payload() -> None:
    subprocess.run(
        [sys.executable, "-m", "scripts.seed_realistic_demo_db"],
        check=True,
    )

    response = client.get(
        "/demo/realistic/analysis",
        params={"latitude": -7.9401, "longitude": -34.8734},
    )

    assert response.status_code == 200
    assert response.json()["selected_transformer"]["transformer_code"] == "TR-001"


def test_realistic_export_endpoint_returns_csv() -> None:
    subprocess.run(
        [sys.executable, "-m", "scripts.seed_realistic_demo_db"],
        check=True,
    )

    response = client.get(
        "/demo/realistic/export.csv",
        params={"latitude": -7.9401, "longitude": -34.8734},
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "TR-001" in response.text


def test_realistic_map_endpoint_returns_html() -> None:
    subprocess.run(
        [sys.executable, "-m", "scripts.seed_realistic_demo_db"],
        check=True,
    )

    response = client.get(
        "/demo/realistic/map",
        params={"latitude": -7.9401, "longitude": -34.8734},
    )

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Mapa Realista" in response.text
    assert "TR-001" in response.text