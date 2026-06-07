import json
import sqlite3
from pathlib import Path

from src.aerial_housing_detection.ml.synthetic_loss_heatmap import (
    SyntheticLossHeatmapBuilder,
    build_feeder_heatmap_row,
    build_heatmap_summary,
    build_transformer_heatmap_row,
    calculate_heat_score,
    classify_heat_level,
)


def test_calculate_heat_score_and_level() -> None:
    high_score = calculate_heat_score(
        perda_kwh=15000,
        perda_percentual=0.35,
        irregularidades=10,
        consumo=80000,
    )

    medium_score = calculate_heat_score(
        perda_kwh=8000,
        perda_percentual=0.20,
        irregularidades=4,
        consumo=40000,
    )

    low_score = calculate_heat_score(
        perda_kwh=500,
        perda_percentual=0.02,
        irregularidades=0,
        consumo=5000,
    )

    assert high_score == 1.0
    assert classify_heat_level(high_score) == "ALTO"
    assert classify_heat_level(medium_score) == "MEDIO"
    assert classify_heat_level(low_score) == "BAIXO"


def test_build_transformer_heatmap_row() -> None:
    row = {
        "codigo_transformador": "TRF-001",
        "codigo_subestacao": "SE-01",
        "codigo_alimentador": "AL-01",
        "mes_referencia": "2025-01",
        "latitude": -8.001,
        "longitude": -34.901,
        "consumo_faturado_kwh": 80000,
        "energia_injetada_total": 1000,
        "perda_estimada_kwh": 15000,
        "perda_estimada_percentual": 0.35,
        "qtd_irregularidades_confirmadas": 10,
        "target_irregularidade_confirmada": 1,
        "nivel_calor": "ALTO",
    }

    result = build_transformer_heatmap_row(row)

    assert result["codigo_transformador"] == "TRF-001"
    assert result["nivel_calor"] == "ALTO"
    assert result["heat_score"] == 1.0
    assert "perda_kwh_elevada" in result["heat_reason"]
    assert "perda_percentual_elevada" in result["heat_reason"]
    assert "irregularidades_confirmadas" in result["heat_reason"]


def test_build_feeder_heatmap_row() -> None:
    row = {
        "codigo_subestacao": "SE-01",
        "codigo_alimentador": "AL-01",
        "mes_referencia": "2025-01",
        "qtd_transformadores": 5,
        "latitude_centroide": -8.002,
        "longitude_centroide": -34.902,
        "consumo_faturado_kwh": 80000,
        "perda_estimada_kwh": 15000,
        "perda_estimada_percentual_media": 0.35,
        "qtd_irregularidades_confirmadas": 10,
        "nivel_calor_alimentador": "ALTO",
    }

    result = build_feeder_heatmap_row(row)

    assert result["codigo_alimentador"] == "AL-01"
    assert result["qtd_transformadores"] == 5
    assert result["nivel_calor_alimentador"] == "ALTO"
    assert result["heat_score"] == 1.0


def test_build_heatmap_summary() -> None:
    transformer_rows = [
        {"nivel_calor": "ALTO", "heat_score": 0.9},
        {"nivel_calor": "MEDIO", "heat_score": 0.5},
        {"nivel_calor": "BAIXO", "heat_score": 0.1},
    ]

    feeder_rows = [
        {"nivel_calor_alimentador": "ALTO", "heat_score": 0.8},
        {"nivel_calor_alimentador": "BAIXO", "heat_score": 0.2},
    ]

    summary = build_heatmap_summary(transformer_rows, feeder_rows)

    assert summary["transformer_rows"] == 3
    assert summary["feeder_rows"] == 2
    assert summary["high_heat_transformers"] == 1
    assert summary["medium_heat_transformers"] == 1
    assert summary["low_heat_transformers"] == 1
    assert summary["high_heat_feeders"] == 1
    assert summary["low_heat_feeders"] == 1
    assert summary["average_transformer_heat_score"] == 0.5
    assert summary["average_feeder_heat_score"] == 0.5


def test_synthetic_loss_heatmap_builder_generates_reports(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "area51.db"
    transformer_path = tmp_path / "transformers.csv"
    feeder_path = tmp_path / "feeders.csv"
    summary_path = tmp_path / "summary.json"

    _create_heatmap_tables(db_path)

    result = SyntheticLossHeatmapBuilder(
        db_path=db_path,
        transformer_heatmap_path=transformer_path,
        feeder_heatmap_path=feeder_path,
        summary_path=summary_path,
    ).run()

    assert result.transformer_rows == 1
    assert result.feeder_rows == 1
    assert result.high_heat_transformers == 1
    assert result.high_heat_feeders == 1

    assert transformer_path.exists()
    assert feeder_path.exists()
    assert summary_path.exists()

    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["transformer_rows"] == 1
    assert summary["feeder_rows"] == 1
    assert summary["high_heat_transformers"] == 1
    assert summary["high_heat_feeders"] == 1


def test_synthetic_loss_heatmap_builder_handles_missing_database(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing.db"
    transformer_path = tmp_path / "transformers.csv"
    feeder_path = tmp_path / "feeders.csv"
    summary_path = tmp_path / "summary.json"

    result = SyntheticLossHeatmapBuilder(
        db_path=db_path,
        transformer_heatmap_path=transformer_path,
        feeder_heatmap_path=feeder_path,
        summary_path=summary_path,
    ).run()

    assert result.transformer_rows == 0
    assert result.feeder_rows == 0
    assert result.high_heat_transformers == 0
    assert result.high_heat_feeders == 0

    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary["transformer_rows"] == 0
    assert summary["feeder_rows"] == 0


def _create_heatmap_tables(db_path: Path) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE synthetic_transformer_heatmap (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                mes_referencia TEXT,
                latitude REAL,
                longitude REAL,
                consumo_faturado_kwh REAL,
                energia_injetada_total REAL,
                perda_estimada_kwh REAL,
                perda_estimada_percentual REAL,
                qtd_irregularidades_confirmadas INTEGER,
                target_irregularidade_confirmada INTEGER,
                nivel_calor TEXT
            )
            """
        )

        connection.execute(
            """
            INSERT INTO synthetic_transformer_heatmap (
                codigo_transformador,
                codigo_subestacao,
                codigo_alimentador,
                mes_referencia,
                latitude,
                longitude,
                consumo_faturado_kwh,
                energia_injetada_total,
                perda_estimada_kwh,
                perda_estimada_percentual,
                qtd_irregularidades_confirmadas,
                target_irregularidade_confirmada,
                nivel_calor
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "TRF-001",
                "SE-01",
                "AL-01",
                "2025-01",
                -8.001,
                -34.901,
                80000,
                1000,
                15000,
                0.35,
                10,
                1,
                "ALTO",
            ),
        )

        connection.execute(
            """
            CREATE TABLE synthetic_feeder_heatmap (
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                mes_referencia TEXT,
                qtd_transformadores INTEGER,
                latitude_centroide REAL,
                longitude_centroide REAL,
                consumo_faturado_kwh REAL,
                perda_estimada_kwh REAL,
                perda_estimada_percentual_media REAL,
                qtd_irregularidades_confirmadas INTEGER,
                nivel_calor_alimentador TEXT
            )
            """
        )

        connection.execute(
            """
            INSERT INTO synthetic_feeder_heatmap (
                codigo_subestacao,
                codigo_alimentador,
                mes_referencia,
                qtd_transformadores,
                latitude_centroide,
                longitude_centroide,
                consumo_faturado_kwh,
                perda_estimada_kwh,
                perda_estimada_percentual_media,
                qtd_irregularidades_confirmadas,
                nivel_calor_alimentador
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "SE-01",
                "AL-01",
                "2025-01",
                5,
                -8.002,
                -34.902,
                80000,
                15000,
                0.35,
                10,
                "ALTO",
            ),
        )
