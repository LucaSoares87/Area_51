from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from src.aerial_housing_detection.api.main import app


def create_image_bytes() -> BytesIO:
    """Create a valid in-memory PNG image."""
    image_bytes = BytesIO()
    image = Image.new("RGB", (1024, 768), color="white")
    image.save(image_bytes, format="PNG")
    image_bytes.seek(0)
    return image_bytes


def test_detect_endpoint_accepts_image_upload() -> None:
    client = TestClient(app)

    response = client.post(
        "/detect",
        files={"file": ("area.png", create_image_bytes(), "image/png")},
    )

    assert response.status_code == 201

    data = response.json()
    assert data["analysis_id"]
    assert data["estimated_residences"] >= 1
    assert data["roof_count"] >= 1
    assert 0 <= data["confidence_score"] <= 1
    assert data["csv_report_path"].endswith(".csv")
    assert data["html_map_path"].endswith(".html")


def test_detect_endpoint_rejects_missing_filename() -> None:
    client = TestClient(app)

    response = client.post(
        "/detect",
        files={"file": ("", create_image_bytes(), "image/png")},
    )

    assert response.status_code in {400, 422}
