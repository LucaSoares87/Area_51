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


def test_synthetic_loss_agent_dashboard_contains_phase_57a_context_blocks() -> None:
    response = client.get("/app/synthetic-loss-agent")

    assert response.status_code == 200
    assert "Contexto operacional" in response.text
    assert "context-feeder" in response.text
    assert "context-substation" in response.text
    assert "context-agent-status" in response.text
    assert "context-updated-at" in response.text


def test_synthetic_loss_agent_dashboard_contains_phase_57a_filters() -> None:
    response = client.get("/app/synthetic-loss-agent")

    assert response.status_code == 200
    assert "Filtros visuais" in response.text
    assert 'data-heat-filter="TODOS"' in response.text
    assert 'data-heat-filter="ALTO"' in response.text
    assert 'data-heat-filter="MEDIO"' in response.text
    assert 'data-heat-filter="BAIXO"' in response.text


def test_synthetic_loss_agent_dashboard_contains_phase_57a_operational_cards() -> None:
    response = client.get("/app/synthetic-loss-agent")

    assert response.status_code == 200
    assert "critical-section" in response.text
    assert "critical-recloser" in response.text
    assert "critical-transformer" in response.text
    assert "high-heat-count" in response.text
    assert "real-notes-count" in response.text
    assert "unproductive-notes-count" in response.text
    assert "fraud-procedure-count" in response.text
    assert "recovered-kwh" in response.text


def test_synthetic_loss_agent_dashboard_contains_phase_57a_tables() -> None:
    response = client.get("/app/synthetic-loss-agent")

    assert response.status_code == 200
    assert "recloser-list" in response.text
    assert "transformers-table-body" in response.text
    assert "suspicious-installations-table-body" in response.text
    assert "Instalações sintéticas suspeitas" in response.text
    assert "Indicadores inspirados em notas, consumo, MMGD e recuperação" in response.text


def test_synthetic_loss_agent_dashboard_static_css_loads() -> None:
    response = client.get("/app/static/synthetic_loss_agent.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert ".page-shell" in response.text
    assert ".context-panel" in response.text
    assert ".filter-chip" in response.text
    assert ".recloser-card" in response.text
    assert ".risk-score" in response.text


def test_synthetic_loss_agent_dashboard_static_js_loads() -> None:
    response = client.get("/app/static/synthetic_loss_agent.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert "synthetic-feeder-operational/summary" in response.text
    assert "renderMap" in response.text
    assert "renderReclosers" in response.text
    assert "renderSuspiciousInstallationsTable" in response.text
    assert "buildSyntheticSuspiciousInstallations" in response.text
    assert "calculateSyntheticRiskScore" in response.text


def test_synthetic_loss_agent_dashboard_route_is_not_in_openapi_schema() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    paths = schema["paths"]

    assert "/app/synthetic-loss-agent" not in paths
