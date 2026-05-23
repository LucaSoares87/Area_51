from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from src.aerial_housing_detection.api.main import app


def create_test_image(path: Path) -> Path:
    """Create a valid test image."""
    image = Image.new("RGB", (1024, 768), color="white")
    image.save(path)
    return path


def test_report_endpoint_generates_outputs(tmp_path: Path) -> None:
    client = TestClient(app)
    image_path = create_test_image(tmp_path / "area_report.png")

    response = client.post(
        "/report",
        json={"image_path": str(image_path)},
    )

    assert response.status_code == 201

    data = response.json()
    assert data["analysis_id"]
    assert data["estimated_residences"] >= 1
    assert data["roof_count"] >= 1
    assert data["csv_report_path"].endswith(".csv")
    assert data["html_map_path"].endswith(".html")


def test_report_endpoint_returns_404_for_missing_image() -> None:
    client = TestClient(app)

    response = client.post(
        "/report",
        json={"image_path": "data/raw/image_that_does_not_exist.png"},
    )

    assert response.status_code == 404
