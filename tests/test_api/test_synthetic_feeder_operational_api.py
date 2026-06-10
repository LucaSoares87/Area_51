from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch
from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app

client = TestClient(app)


def test_synthetic_feeder_operational_health_endpoint_returns_ok() -> None:
    response = client.get("/synthetic-feeder-operational/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["service"] == "synthetic_feeder_operational"


def test_synthetic_feeder_operational_run_endpoint_returns_summary(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _patch_paths(tmp_path, monkeypatch)

    response = client.post("/synthetic-feeder-operational/run")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "success"
    assert payload["substations"] == 1
    assert payload["feeders"] == 1
    assert payload["route_points"] == 11
    assert payload["reclosers"] == 3
    assert payload["mv_customers"] == 9
    assert payload["transformers"] == 60
    assert payload["sections"] == 4


def test_synthetic_feeder_operational_summary_endpoint_returns_dashboard_data(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _patch_paths(tmp_path, monkeypatch)

    response = client.get("/synthetic-feeder-operational/summary")

    assert response.status_code == 200

    payload = response.json()

    assert payload["codigo_subestacao"] == "HPO"
    assert payload["codigo_alimentador"] == "HPO-0IL4"
    assert payload["extensao_rede_km"] == 6.0
    assert payload["total_uc_mt"] == 9
    assert payload["total_transformadores"] == 60
    assert payload["total_religadores"] == 3
    assert payload["total_uc_bt"] > 0
    assert payload["total_gd"] > 0
    assert payload["perda_estimada_gwh"] > 0
    assert len(payload["sections"]) == 4
    assert len(payload["reclosers"]) == 3


def test_synthetic_feeder_operational_route_endpoint_returns_path_points(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _patch_paths(tmp_path, monkeypatch)

    response = client.get("/synthetic-feeder-operational/route")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_rows"] == 11
    assert len(payload["items"]) == 11
    assert payload["items"][0]["tipo_ponto"] == "subestacao"
    assert payload["items"][0]["descricao"] == "Saída da Subestação HPO"


def test_synthetic_feeder_operational_sections_endpoint_returns_sections(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _patch_paths(tmp_path, monkeypatch)

    response = client.get("/synthetic-feeder-operational/sections")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_rows"] == 4
    assert len(payload["items"]) == 4
    assert payload["items"][0]["codigo_secao"] == "SEC-01"
    assert payload["items"][0]["codigo_alimentador"] == "HPO-0IL4"


def test_synthetic_feeder_operational_reclosers_endpoint_returns_reclosers(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _patch_paths(tmp_path, monkeypatch)

    response = client.get("/synthetic-feeder-operational/reclosers")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_rows"] == 3
    assert len(payload["items"]) == 3
    assert payload["items"][0]["codigo_religador"] == "RLG-01"
    assert payload["items"][0]["transformadores_jusante"] > 0


def test_synthetic_feeder_operational_transformers_endpoint_returns_limited_items(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _patch_paths(tmp_path, monkeypatch)

    response = client.get("/synthetic-feeder-operational/transformers?limit=5")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_rows"] == 60
    assert payload["limit"] == 5
    assert len(payload["items"]) == 5
    assert payload["items"][0]["codigo_transformador"] == "TRF-HPO-0IL4-001"


def test_synthetic_feeder_operational_mv_customers_endpoint_returns_customers(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _patch_paths(tmp_path, monkeypatch)

    response = client.get("/synthetic-feeder-operational/mv-customers")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_rows"] == 9
    assert len(payload["items"]) == 9
    assert payload["items"][0]["codigo_cliente_mt"] == "MT-HPO-0IL4-001"


def test_synthetic_feeder_operational_substations_endpoint_returns_substation(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _patch_paths(tmp_path, monkeypatch)

    response = client.get("/synthetic-feeder-operational/substations")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_rows"] == 1
    assert payload["items"][0]["codigo_subestacao"] == "HPO"


def test_synthetic_feeder_operational_feeders_endpoint_returns_feeder(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    _patch_paths(tmp_path, monkeypatch)

    response = client.get("/synthetic-feeder-operational/feeders")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_rows"] == 1
    assert payload["items"][0]["codigo_alimentador"] == "HPO-0IL4"
    assert payload["items"][0]["total_religadores"] == 3


def _patch_paths(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    db_path = tmp_path / "area51.db"
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(exist_ok=True)

    monkeypatch.setattr(
        "src.aerial_housing_detection.api.routes.synthetic_feeder_operational.DB_PATH",
        db_path,
    )
    monkeypatch.setattr(
        "src.aerial_housing_detection.api.routes.synthetic_feeder_operational.SUMMARY_PATH",
        reports_dir / "synthetic_feeder_operational_summary.json",
    )
    monkeypatch.setattr(
        "src.aerial_housing_detection.api.routes.synthetic_feeder_operational.ROUTE_PATH",
        reports_dir / "synthetic_feeder_operational_route.csv",
    )
    monkeypatch.setattr(
        "src.aerial_housing_detection.api.routes.synthetic_feeder_operational.SECTIONS_PATH",
        reports_dir / "synthetic_feeder_operational_sections.csv",
    )
