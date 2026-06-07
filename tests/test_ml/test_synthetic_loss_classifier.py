import json
import sqlite3
from pathlib import Path

from src.aerial_housing_detection.ml.synthetic_loss_classifier import (
    SyntheticLossClassifier,
    build_synthetic_loss_metrics,
    precision_at_k,
    recall_at_k,
    score_synthetic_loss_row,
)


def test_score_synthetic_loss_row_generates_probability_and_prediction() -> None:
    row = {
        "codigo_transformador": "TRF-001",
        "codigo_subestacao": "SE-01",
        "codigo_alimentador": "AL-01",
        "mes_referencia": "2025-01",
        "consumo_faturado_kwh": 25000,
        "energia_injetada_total": 2000,
        "qtd_inspecoes": 6,
        "qtd_irregularidades_confirmadas": 4,
        "qtd_defeitos_concessionaria": 1,
        "qtd_sem_perdas": 0,
        "qtd_normais": 0,
        "qtd_casas_cras": 150,
        "qtd_casas_ibge": 140,
        "qtd_casas_telhado": 160,
        "media_estimativa_casas": 150,
        "divergencia_casas_clientes": 50,
        "perda_estimada_kwh": 6000,
        "perda_estimada_percentual": 0.30,
        "target_irregularidade_confirmada": 1,
    }

    scored = score_synthetic_loss_row(row)

    assert scored["loss_probability"] > 0.5
    assert scored["predicted_irregularity"] == 1
    assert scored["model_name"] == "synthetic_rule_based_loss_classifier"
    assert scored["model_stage"] == "synthetic_supervised_baseline"


def test_precision_and_recall_at_k() -> None:
    rows = [
        {"target_irregularidade_confirmada": 1},
        {"target_irregularidade_confirmada": 1},
        {"target_irregularidade_confirmada": 0},
        {"target_irregularidade_confirmada": 1},
    ]

    assert precision_at_k(rows, 2) == 1.0
    assert precision_at_k(rows, 4) == 0.75
    assert recall_at_k(rows, 2) == 0.666667
    assert recall_at_k(rows, 4) == 1.0


def test_build_synthetic_loss_metrics() -> None:
    rows = [
        {"target_irregularidade_confirmada": 1},
        {"target_irregularidade_confirmada": 0},
        {"target_irregularidade_confirmada": 1},
        {"target_irregularidade_confirmada": 0},
    ]

    metrics = build_synthetic_loss_metrics(rows)

    assert metrics["total_rows"] == 4
    assert metrics["positive_rows"] == 2
    assert metrics["positive_rate"] == 0.5
    assert metrics["precision_at_10"] == 0.5
    assert metrics["precision_at_50"] == 0.5
    assert metrics["recall_at_50"] == 1.0


def test_synthetic_loss_classifier_generates_metrics_and_ranking(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "area51.db"
    metrics_path = tmp_path / "metrics.json"
    ranking_path = tmp_path / "ranking.csv"

    _create_dataset(db_path)

    result = SyntheticLossClassifier(
        db_path=db_path,
        metrics_path=metrics_path,
        ranking_path=ranking_path,
    ).run()

    assert result.total_rows == 3
    assert result.positive_rows == 1
    assert result.precision_at_10 == 0.333333
    assert result.recall_at_50 == 1.0
    assert metrics_path.exists()
    assert ranking_path.exists()

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    ranking = ranking_path.read_text(encoding="utf-8")

    assert metrics["total_rows"] == 3
    assert "loss_probability" in ranking
    assert "predicted_irregularity" in ranking


def test_synthetic_loss_classifier_handles_missing_database(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing.db"
    metrics_path = tmp_path / "metrics.json"
    ranking_path = tmp_path / "ranking.csv"

    result = SyntheticLossClassifier(
        db_path=db_path,
        metrics_path=metrics_path,
        ranking_path=ranking_path,
    ).run()

    assert result.total_rows == 0
    assert result.positive_rows == 0
    assert result.precision_at_10 == 0.0
    assert result.precision_at_50 == 0.0
    assert result.recall_at_50 == 0.0
    assert metrics_path.exists()
    assert ranking_path.exists()


def _create_dataset(db_path: Path) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE synthetic_loss_agent_dataset (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                mes_referencia TEXT,
                latitude REAL,
                longitude REAL,
                qtd_clientes_vinculados INTEGER,
                qtd_clientes_com_consumo INTEGER,
                consumo_faturado_kwh REAL,
                qtd_instalacoes_gd INTEGER,
                energia_injetada_total REAL,
                qtd_inspecoes INTEGER,
                qtd_irregularidades_confirmadas INTEGER,
                qtd_defeitos_concessionaria INTEGER,
                qtd_sem_perdas INTEGER,
                qtd_normais INTEGER,
                qtd_casas_cras INTEGER,
                qtd_casas_ibge INTEGER,
                qtd_casas_telhado INTEGER,
                media_estimativa_casas REAL,
                divergencia_casas_clientes REAL,
                nivel_divergencia_habitacional TEXT,
                perda_estimada_kwh REAL,
                perda_estimada_percentual REAL,
                nivel_calor TEXT,
                target_irregularidade_confirmada INTEGER,
                prioridade_ml_operacional TEXT
            )
            """
        )

        connection.executemany(
            """
            INSERT INTO synthetic_loss_agent_dataset (
                codigo_transformador,
                codigo_subestacao,
                codigo_alimentador,
                mes_referencia,
                latitude,
                longitude,
                qtd_clientes_vinculados,
                qtd_clientes_com_consumo,
                consumo_faturado_kwh,
                qtd_instalacoes_gd,
                energia_injetada_total,
                qtd_inspecoes,
                qtd_irregularidades_confirmadas,
                qtd_defeitos_concessionaria,
                qtd_sem_perdas,
                qtd_normais,
                qtd_casas_cras,
                qtd_casas_ibge,
                qtd_casas_telhado,
                media_estimativa_casas,
                divergencia_casas_clientes,
                nivel_divergencia_habitacional,
                perda_estimada_kwh,
                perda_estimada_percentual,
                nivel_calor,
                target_irregularidade_confirmada,
                prioridade_ml_operacional
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "TRF-001",
                    "SE-01",
                    "AL-01",
                    "2025-01",
                    -8.001,
                    -34.901,
                    120,
                    118,
                    25000,
                    2,
                    2000,
                    6,
                    4,
                    1,
                    0,
                    0,
                    150,
                    140,
                    160,
                    150,
                    50,
                    "ALTA_DIVERGENCIA",
                    6000,
                    0.30,
                    "ALTO",
                    1,
                    "ALTA",
                ),
                (
                    "TRF-002",
                    "SE-01",
                    "AL-01",
                    "2025-01",
                    -8.002,
                    -34.902,
                    100,
                    99,
                    8000,
                    0,
                    0,
                    1,
                    0,
                    0,
                    1,
                    0,
                    102,
                    101,
                    103,
                    102,
                    2,
                    "BAIXA_DIVERGENCIA",
                    300,
                    0.03,
                    "BAIXO",
                    0,
                    "BAIXA",
                ),
                (
                    "TRF-003",
                    "SE-01",
                    "AL-02",
                    "2025-01",
                    -8.003,
                    -34.903,
                    80,
                    80,
                    7000,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    1,
                    80,
                    81,
                    82,
                    81,
                    1,
                    "BAIXA_DIVERGENCIA",
                    200,
                    0.02,
                    "BAIXO",
                    0,
                    "BAIXA",
                ),
            ],
        )
