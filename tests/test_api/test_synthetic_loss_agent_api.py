from pathlib import Path

from fastapi.testclient import TestClient

from src.aerial_housing_detection.api.main import app
from src.aerial_housing_detection.ml.synthetic_loss_agent_dataset import (
    SyntheticLossAgentDatasetImporter,
)

client = TestClient(app)


def test_synthetic_loss_agent_health_endpoint_returns_ok() -> None:
    response = client.get("/synthetic-loss-agent/health")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["service"] == "synthetic_loss_agent"


def test_synthetic_loss_agent_run_endpoint_returns_pipeline_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _prepare_synthetic_database(tmp_path, monkeypatch)

    response = client.post("/synthetic-loss-agent/run")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "success"
    assert payload["classifier"]["total_rows"] == 1
    assert payload["classifier"]["positive_rows"] == 1
    assert payload["heatmap"]["transformer_rows"] == 1
    assert payload["heatmap"]["feeder_rows"] == 1
    assert payload["map"]["transformer_points"] == 1
    assert payload["map"]["feeder_points"] == 1


def test_synthetic_loss_agent_metrics_endpoint_returns_metrics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _prepare_synthetic_database(tmp_path, monkeypatch)

    response = client.get("/synthetic-loss-agent/metrics")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_rows"] == 1
    assert payload["positive_rows"] == 1
    assert payload["precision_at_10"] == 1.0


def test_synthetic_loss_agent_ranking_endpoint_returns_limited_items(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _prepare_synthetic_database(tmp_path, monkeypatch)

    response = client.get("/synthetic-loss-agent/ranking?limit=1")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_rows"] == 1
    assert payload["limit"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["codigo_transformador"] == "TRF-001"


def test_synthetic_loss_agent_transformer_heatmap_endpoint_returns_items(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _prepare_synthetic_database(tmp_path, monkeypatch)

    response = client.get("/synthetic-loss-agent/heatmap/transformers?limit=1")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_rows"] == 1
    assert payload["limit"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["codigo_transformador"] == "TRF-001"


def test_synthetic_loss_agent_feeder_heatmap_endpoint_returns_items(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _prepare_synthetic_database(tmp_path, monkeypatch)

    response = client.get("/synthetic-loss-agent/heatmap/feeders?limit=1")

    assert response.status_code == 200

    payload = response.json()

    assert payload["total_rows"] == 1
    assert payload["limit"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["codigo_alimentador"] == "AL-01"


def test_synthetic_loss_agent_heatmap_summary_endpoint_returns_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _prepare_synthetic_database(tmp_path, monkeypatch)

    response = client.get("/synthetic-loss-agent/heatmap/summary")

    assert response.status_code == 200

    payload = response.json()

    assert payload["transformer_rows"] == 1
    assert payload["feeder_rows"] == 1


def test_synthetic_loss_agent_map_endpoint_returns_html(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _prepare_synthetic_database(tmp_path, monkeypatch)

    response = client.get("/synthetic-loss-agent/map")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Area 51 - Mapa Sintético de Perdas" in response.text
    assert "TRF-001" in response.text


def _prepare_synthetic_database(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "area51.db"
    source_dir = tmp_path / "synthetic_ml"
    reports_dir = tmp_path / "reports"

    source_dir.mkdir()
    reports_dir.mkdir()

    _write_synthetic_csvs(source_dir)

    monkeypatch.setattr(
        "src.aerial_housing_detection.api.routes.synthetic_loss_agent.DB_PATH",
        db_path,
    )
    monkeypatch.setattr(
        "src.aerial_housing_detection.api.routes.synthetic_loss_agent.METRICS_PATH",
        reports_dir / "synthetic_loss_classifier_metrics.json",
    )
    monkeypatch.setattr(
        "src.aerial_housing_detection.api.routes.synthetic_loss_agent.RANKING_PATH",
        reports_dir / "synthetic_loss_classifier_ranking.csv",
    )
    monkeypatch.setattr(
        "src.aerial_housing_detection.api.routes.synthetic_loss_agent.TRANSFORMER_HEATMAP_PATH",
        reports_dir / "synthetic_loss_heatmap_transformers.csv",
    )
    monkeypatch.setattr(
        "src.aerial_housing_detection.api.routes.synthetic_loss_agent.FEEDER_HEATMAP_PATH",
        reports_dir / "synthetic_loss_heatmap_feeders.csv",
    )
    monkeypatch.setattr(
        "src.aerial_housing_detection.api.routes.synthetic_loss_agent.HEATMAP_SUMMARY_PATH",
        reports_dir / "synthetic_loss_heatmap_summary.json",
    )
    monkeypatch.setattr(
        "src.aerial_housing_detection.api.routes.synthetic_loss_agent.MAP_PATH",
        reports_dir / "synthetic_loss_heatmap_map.html",
    )

    SyntheticLossAgentDatasetImporter(
        db_path=db_path,
        source_dir=source_dir,
    ).run()


def _write_synthetic_csvs(source_dir: Path) -> None:
    _write_file(
        source_dir / "fake_dataset_agente_perdas_transformador_mes.csv",
        (
            "codigo_transformador,codigo_subestacao,codigo_alimentador,"
            "mes_referencia,latitude,longitude,qtd_clientes_vinculados,"
            "qtd_clientes_com_consumo,consumo_faturado_kwh,qtd_instalacoes_gd,"
            "energia_injetada_total,qtd_inspecoes,qtd_irregularidades_confirmadas,"
            "qtd_defeitos_concessionaria,qtd_sem_perdas,qtd_normais,"
            "qtd_casas_cras,qtd_casas_ibge,qtd_casas_telhado,"
            "media_estimativa_casas,divergencia_casas_clientes,"
            "nivel_divergencia_habitacional,perda_estimada_kwh,"
            "perda_estimada_percentual,nivel_calor,"
            "target_irregularidade_confirmada,prioridade_ml_operacional\n"
            "TRF-001,SE-01,AL-01,2025-01,-8.001,-34.901,120,118,25000,2,"
            "2000,6,4,1,0,0,150,140,160,150,50,ALTA_DIVERGENCIA,"
            "6000,0.30,ALTO,1,ALTA\n"
        ),
    )

    _write_file(
        source_dir / "fake_heatmap_transformador_mes.csv",
        (
            "codigo_transformador,codigo_subestacao,codigo_alimentador,"
            "mes_referencia,latitude,longitude,consumo_faturado_kwh,"
            "energia_injetada_total,perda_estimada_kwh,"
            "perda_estimada_percentual,qtd_irregularidades_confirmadas,"
            "target_irregularidade_confirmada,nivel_calor\n"
            "TRF-001,SE-01,AL-01,2025-01,-8.001,-34.901,25000,2000,"
            "6000,0.30,4,1,ALTO\n"
        ),
    )

    _write_file(
        source_dir / "fake_heatmap_alimentador_mes.csv",
        (
            "codigo_subestacao,codigo_alimentador,mes_referencia,"
            "qtd_transformadores,latitude_centroide,longitude_centroide,"
            "consumo_faturado_kwh,perda_estimada_kwh,"
            "perda_estimada_percentual_media,qtd_irregularidades_confirmadas,"
            "nivel_calor_alimentador\n"
            "SE-01,AL-01,2025-01,5,-8.002,-34.902,80000,12000,0.25,8,ALTO\n"
        ),
    )

    _write_file(
        source_dir / "fake_estimativa_casas_transformador.csv",
        (
            "codigo_transformador,codigo_subestacao,codigo_alimentador,"
            "latitude,longitude,qtd_clientes_cadastrados,qtd_casas_cras,"
            "qtd_casas_ibge,qtd_casas_telhado,media_estimativa_casas,"
            "divergencia_casas_clientes,nivel_divergencia_habitacional\n"
            "TRF-001,SE-01,AL-01,-8.001,-34.901,120,150,140,160,150,30,"
            "ALTA_DIVERGENCIA\n"
        ),
    )

    _write_file(
        source_dir / "fake_labels_irregularidade_transformador_mes.csv",
        (
            "codigo_transformador,codigo_subestacao,codigo_alimentador,"
            "mes_referencia,qtd_inspecoes,qtd_instalacoes_inspecionadas,"
            "qtd_irregularidades_confirmadas,qtd_defeitos_concessionaria,"
            "qtd_sem_perdas,qtd_normais,target_irregularidade_confirmada\n"
            "TRF-001,SE-01,AL-01,2025-01,6,4,4,1,0,0,1\n"
        ),
    )


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
