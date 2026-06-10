from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app

client = TestClient(app)


def test_synthetic_loss_agent_dashboard_page_loads() -> None:
    response = client.get("/app/synthetic-loss-agent")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Area 51 - Painel Operacional do Alimentador" in response.text
    assert "Ação - Modelo Alimentador" in response.text
    assert "synthetic_loss_agent.css" in response.text
    assert "synthetic_loss_agent.js" in response.text


def test_synthetic_loss_agent_dashboard_static_css_loads() -> None:
    response = client.get("/app/static/synthetic_loss_agent.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert ".page-shell" in response.text
    assert ".map-canvas" in response.text
    assert ".metric-card" in response.text


def test_synthetic_loss_agent_dashboard_static_js_loads() -> None:
    response = client.get("/app/static/synthetic_loss_agent.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert "synthetic-feeder-operational/summary" in response.text
    assert "renderMap" in response.text
    assert "renderReclosers" in response.text


def test_synthetic_loss_agent_dashboard_route_is_not_in_openapi_schema() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    paths = schema["paths"]

    assert "/app/synthetic-loss-agent" not in paths