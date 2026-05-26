from pathlib import Path

from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app

client = TestClient(app)


def test_roof_upload_endpoint_accepts_image_upload(tmp_path: Path) -> None:
    image_path = tmp_path / "roof.png"
    image_path.write_bytes(

            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01"
            b"\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00"
            b"\x90wS\xde"
            b"\x00\x00\x00\x0cIDAT"
            b"\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfe"
            b"A\xe2!\xbc"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"

    )

    with image_path.open("rb") as image_file:
        response = client.post(
            "/roof/upload",
            files={"file": ("roof.png", image_file, "image/png")},
        )

    assert response.status_code == 201

    data = response.json()

    assert data["filename"] == "roof.png"
    assert data["content_type"] == "image/png"
    assert "analysis_id" in data
    assert "estimated_roofs" in data
    assert "confidence_score" in data
    assert data["status"] == "completed"


def test_roof_upload_endpoint_rejects_non_image_file() -> None:
    response = client.post(
        "/roof/upload",
        files={"file": ("document.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file must be an image."
