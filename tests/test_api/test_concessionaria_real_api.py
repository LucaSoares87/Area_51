from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app

client = TestClient(app)


def test_concessionaria_real_analysis_not_found_without_import() -> None:
    response = client.get(
        "/concessionaria/real/analysis",
        params={"transformer_code": "TRANSFORMADOR_INEXISTENTE"},
    )

    assert response.status_code == 200
    assert response.json()["found"] is False


def test_concessionaria_real_export_returns_csv() -> None:
    response = client.get(
        "/concessionaria/real/export.csv",
        params={"transformer_code": "TRANSFORMADOR_INEXISTENTE"},
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "codigo_transformador" in response.text
