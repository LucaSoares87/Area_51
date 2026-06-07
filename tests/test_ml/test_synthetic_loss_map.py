import sqlite3
from pathlib import Path

from src.aerial_housing_detection.ml.synthetic_loss_map import (
    SyntheticLossMapBuilder,
    build_feeder_map_point,
    build_map_html,
    build_transformer_map_point,
)


def test_build_transformer_map_point() -> None:
    row = {
        "codigo_transformador": "TRF-001",
        "codigo_subestacao": "SE-01",
        "codigo_alimentador": "AL-01",
        "mes_referencia": "2025-01",
        "latitude": -8.001,
        "longitude": -34.901,
        "consumo_faturado_kwh": 15000,
        "energia_injetada_total": 500,
        "perda_estimada_kwh": 3000,
        "perda_estimada_percentual": 0.2,
        "qtd_irregularidades_confirmadas": 2,
        "target_irregularidade_confirmada": 1,
        "nivel_calor": "ALTO",
    }

    point = build_transformer_map_point(row)

    assert point["tipo"] == "transformador"
    assert point["codigo"] == "TRF-001"
    assert point["nivel_calor"] == "ALTO"
    assert point["intensidade"] == 100
    assert point["latitude"] == -8.001
    assert point["longitude"] == -34.901


def test_build_feeder_map_point() -> None:
    row = {
        "codigo_subestacao": "SE-01",
        "codigo_alimentador": "AL-01",
        "mes_referencia": "2025-01",
        "qtd_transformadores": 5,
        "latitude_centroide": -8.002,
        "longitude_centroide": -34.902,
        "consumo_faturado_kwh": 80000,
        "perda_estimada_kwh": 12000,
        "perda_estimada_percentual_media": 0.25,
        "qtd_irregularidades_confirmadas": 8,
        "nivel_calor_alimentador": "MEDIO",
    }

    point = build_feeder_map_point(row)

    assert point["tipo"] == "alimentador"
    assert point["codigo"] == "AL-01"
    assert point["nivel_calor"] == "MEDIO"
    assert point["intensidade"] == 60
    assert point["qtd_transformadores"] == 5


def test_build_map_html_contains_dashboard_and_points() -> None:
    transformer_points = [
        {
            "tipo": "transformador",
            "codigo": "TRF-001",
            "codigo_subestacao": "SE-01",
            "codigo_alimentador": "AL-01",
            "mes_referencia": "2025-01",
            "latitude": -8.001,
            "longitude": -34.901,
            "consumo_faturado_kwh": 15000,
            "energia_injetada_total": 500,
            "perda_estimada_kwh": 3000,
            "perda_estimada_percentual": 0.2,
            "qtd_irregularidades_confirmadas": 2,
            "target_irregularidade_confirmada": 1,
            "nivel_calor": "ALTO",
            "intensidade": 100,
        }
    ]
    feeder_points = [
        {
            "tipo": "alimentador",
            "codigo": "AL-01",
            "codigo_subestacao": "SE-01",
            "codigo_alimentador": "AL-01",
            "mes_referencia": "2025-01",
            "latitude": -8.002,
            "longitude": -34.902,
            "qtd_transformadores": 5,
            "consumo_faturado_kwh": 80000,
            "perda_estimada_kwh": 12000,
            "perda_estimada_percentual": 0.25,
            "qtd_irregularidades_confirmadas": 8,
            "nivel_calor": "MEDIO",
            "intensidade": 60,
        }
    ]

    html = build_map_html(transformer_points, feeder_points)

    assert "Area 51 - Mapa Sintético de Perdas" in html
    assert "TRF-001" in html
    assert "AL-01" in html
    assert "transformer_points" in html
    assert "feeder_points" in html


def test_synthetic_loss_map_builder_generates_html_report(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "area51.db"
    map_path = tmp_path / "map.html"

    _create_map_tables(db_path)

    result = SyntheticLossMapBuilder(
        db_path=db_path,
        map_path=map_path,
    ).run()

    assert result.transformer_points == 1
    assert result.feeder_points == 1
    assert result.high_heat_transformers == 1
    assert result.high_heat_feeders == 1
    assert map_path.exists()

    content = map_path.read_text(encoding="utf-8")

    assert "Area 51 - Mapa Sintético de Perdas" in content
    assert "TRF-001" in content
    assert "AL-01" in content


def test_synthetic_loss_map_builder_handles_missing_database(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing.db"
    map_path = tmp_path / "map.html"

    result = SyntheticLossMapBuilder(
        db_path=db_path,
        map_path=map_path,
    ).run()

    assert result.transformer_points == 0
    assert result.feeder_points == 0
    assert result.high_heat_transformers == 0
    assert result.high_heat_feeders == 0
    assert map_path.exists()

    content = map_path.read_text(encoding="utf-8")

    assert "Area 51 - Mapa Sintético de Perdas" in content
    assert "Pontos de transformadores" in content


def _create_map_tables(db_path: Path) -> None:
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
                15000,
                500,
                3000,
                0.2,
                2,
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
                12000,
                0.25,
                8,
                "ALTO",
            ),
        )
