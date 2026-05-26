from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app

client = TestClient(app)


def test_web_app_returns_html_interface() -> None:
    response = client.get("/app")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Interface Operacional" in response.text


def test_web_app_serves_static_assets() -> None:
    response = client.get("/app/static/app.js")

    assert response.status_code == 200
    assert "function searchTransformer" in response.text
