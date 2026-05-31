import csv
import sqlite3
from pathlib import Path

from src.aerial_housing_detection.ml.dataset_builder import (
    TransformerMlDatasetBuilder,
)


def test_ml_dataset_builder_creates_dataset_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "area51.db"
    output_path = tmp_path / "ml_transformer_dataset.csv"
    _create_feature_store_database(db_path)

    result = TransformerMlDatasetBuilder(
        db_path=db_path,
        output_path=output_path,
    ).build()

    assert result.rows_created == 2
    assert output_path.exists()

    rows = list(csv.DictReader(output_path.open("r", encoding="utf-8")))

    assert len(rows) == 2
    assert rows[0]["codigo_transformador"] == "A00001"
    assert rows[0]["target_risco_alto"] == "1"
    assert rows[1]["codigo_transformador"] == "A00002"
    assert rows[1]["target_risco_alto"] == "0"


def test_ml_dataset_builder_returns_empty_when_database_missing(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing.db"
    output_path = tmp_path / "ml_transformer_dataset.csv"

    result = TransformerMlDatasetBuilder(
        db_path=db_path,
        output_path=output_path,
    ).build()

    assert result.rows_created == 0
    assert output_path.exists()

    content = output_path.read_text(encoding="utf-8")

    assert "codigo_transformador" in content


def test_ml_dataset_builder_serializes_csv_header(tmp_path: Path) -> None:
    builder = TransformerMlDatasetBuilder(
        db_path=tmp_path / "missing.db",
        output_path=tmp_path / "dataset.csv",
    )

    content = builder.to_csv([])

    assert "codigo_transformador" in content
    assert "target_risco_alto" in content


def _create_feature_store_database(db_path: Path) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE real_operational_features (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                mes_referencia TEXT,
                latitude REAL,
                longitude REAL,
                qtd_clientes INTEGER,
                qtd_clientes_com_consumo INTEGER,
                qtd_ligado INTEGER,
                qtd_cortado INTEGER,
                qtd_baixado INTEGER,
                consumo_faturado_kwh REAL,
                consumo_medio_por_cliente_ligado REAL,
                qtd_instalacoes_gd INTEGER,
                energia_injetada_total REAL,
                energia_injetada_fora_ponta REAL,
                energia_injetada_ponta REAL,
                qtd_notas INTEGER,
                energia_recuperada_media_kwh REAL,
                percentual_cortado REAL,
                percentual_baixado REAL,
                risco_score INTEGER,
                prioridade TEXT
            )
            """
        )

        connection.execute(
            """
            INSERT INTO real_operational_features VALUES (
                'A00001',
                'IGU',
                'IGU-01C2',
                '2025-01',
                -7.95,
                -34.85,
                100,
                90,
                80,
                20,
                5,
                30000,
                375,
                1,
                500,
                480,
                20,
                8,
                1200,
                0.20,
                0.05,
                75,
                'Alta'
            )
            """
        )

        connection.execute(
            """
            INSERT INTO real_operational_features VALUES (
                'A00002',
                'IGU',
                'IGU-01C2',
                '2025-01',
                -7.96,
                -34.86,
                50,
                45,
                45,
                1,
                0,
                9000,
                200,
                0,
                0,
                0,
                0,
                0,
                0,
                0.02,
                0.0,
                20,
                'Baixa'
            )
            """
        )