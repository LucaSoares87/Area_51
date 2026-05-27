from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app

client = TestClient(app)


def test_web_root_redirects_to_login() -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code in {307, 308}
    assert response.headers["location"] == "/login"


def test_web_login_returns_html_interface() -> None:
    response = client.get("/login")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Entrar no sistema" in response.text
    assert "Neoenergia Pernambuco" in response.text
    assert "togglePasswordVisibility" in response.text


def test_web_app_returns_html_interface() -> None:
    response = client.get("/app")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Interface Operacional" in response.text
    assert "Resumo da análise" in response.text


def test_web_app_serves_javascript_asset() -> None:
    response = client.get("/app/static/app.js")

    assert response.status_code == 200
    assert "function searchTransformer" in response.text
    assert "function renderFriendlyResult" in response.text


def test_web_app_serves_css_asset() -> None:
    response = client.get("/app/static/styles.css")

    assert response.status_code == 200
    assert ".summary-card" in response.text


def test_web_login_serves_javascript_asset() -> None:
    response = client.get("/app/static/login.js")

    assert response.status_code == 200
    assert "function handleLogin" in response.text
    assert "function togglePasswordVisibility" in response.text


def test_web_login_serves_css_asset() -> None:
    response = client.get("/app/static/login.css")

    assert response.status_code == 200
    assert ".login-card" in response.text
    assert ".password-toggle" in response.text
