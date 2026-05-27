from pathlib import Path

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
    assert "Mapa de calor e transformadores" in response.text


def test_web_app_serves_javascript_asset() -> None:
    response = client.get("/app/static/app.js")

    assert response.status_code == 200
    assert "function searchTransformer" in response.text
    assert "function renderFriendlyResult" in response.text
    assert "function openOperationalMap" in response.text


def test_web_app_serves_css_asset() -> None:
    response = client.get("/app/static/styles.css")

    assert response.status_code == 200
    assert ".summary-card" in response.text
    assert ".quick-card" in response.text


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


def test_web_map_returns_404_when_map_was_not_generated(tmp_path: Path) -> None:
    map_path = Path("reports") / "transformer_operational_map.html"

    if map_path.exists():
        map_path.unlink()

    response = client.get("/app/map")

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Mapa operacional ainda não foi gerado. "
        "Execute a geração do mapa antes de acessar esta página."
    )


def test_web_map_returns_generated_map() -> None:
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    map_path = reports_dir / "transformer_operational_map.html"
    map_path.write_text(
        "<html><body>Mapa operacional de transformadores</body></html>",
        encoding="utf-8",
    )

    response = client.get("/app/map")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Mapa operacional de transformadores" in response.text

    map_path.unlink(missing_ok=True)
