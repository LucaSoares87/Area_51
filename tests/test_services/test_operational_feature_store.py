import sqlite3
from pathlib import Path

from src.aerial_housing_detection.services.operational_feature_store import (
    OperationalFeatureStore,
)


def test_operational_feature_store_builds_features(tmp_path: Path) -> None:
    db_path = tmp_path / "area51.db"
    _create_base_database(db_path)

    result = OperationalFeatureStore(db_path=db_path).build()

    assert result.rows_created == 1

    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT
                codigo_transformador,
                mes_referencia,
                qtd_ligado,
                qtd_cortado,
                consumo_faturado_kwh,
                consumo_medio_por_cliente_ligado,
                percentual_cortado,
                risco_score,
                prioridade
            FROM real_operational_features
            """
        ).fetchone()

    assert row == (
    "A00074",
    "2025-01",
    80,
    20,
    24000.0,
    300.0,
    0.2,
    70,
    "Alta",
)


def test_operational_feature_store_returns_ranking(tmp_path: Path) -> None:
    db_path = tmp_path / "area51.db"
    _create_base_database(db_path)
    store = OperationalFeatureStore(db_path=db_path)
    store.build()

    result = store.get_ranking(limit=10)

    assert result["total_records"] == 1
    assert result["records"][0]["codigo_transformador"] == "A00074"


def test_operational_feature_store_exports_csv(tmp_path: Path) -> None:
    db_path = tmp_path / "area51.db"
    _create_base_database(db_path)
    store = OperationalFeatureStore(db_path=db_path)
    store.build()

    content = store.export_csv()

    assert "codigo_transformador" in content
    assert "A00074" in content


def test_operational_feature_store_handles_missing_database(tmp_path: Path) -> None:
    db_path = tmp_path / "missing.db"

    result = OperationalFeatureStore(db_path=db_path).get_ranking()

    assert result["total_records"] == 0
    assert result["records"] == []


def _create_base_database(db_path: Path) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE real_electrical_assets (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                pg_id REAL,
                pg TEXT,
                codigo_ponto_medido TEXT,
                conta_contrato TEXT,
                data_cadastro_gse TEXT,
                data_exclusao TEXT,
                latitude REAL,
                longitude REAL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO real_electrical_assets VALUES (
                'A00074',
                'IGU',
                'IGU-01C2',
                1,
                'PG01',
                'PM01',
                'CC01',
                '2025-01-01',
                NULL,
                -7.95,
                -34.85
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE real_transformer_customers (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                instalacao TEXT,
                conta_contrato TEXT,
                regional TEXT,
                setor TEXT,
                subestacao_cliente TEXT,
                alimentador_cliente TEXT
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO real_transformer_customers VALUES (
                'A00074',
                'IGU',
                'IGU-01C2',
                ?,
                ?,
                'REGIONAL',
                'SETOR',
                'IGU',
                'IGU-01C2'
            )
            """,
            [("0001", "CC01"), ("0002", "CC02")],
        )

        connection.execute(
            """
            CREATE TABLE real_transformer_consumption_monthly (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                mes_referencia TEXT,
                qtd_clientes_com_consumo INTEGER,
                consumo_faturado_kwh REAL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO real_transformer_consumption_monthly VALUES (
                'A00074',
                'IGU',
                'IGU-01C2',
                '2025-01',
                80,
                24000
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE real_transformer_gd_monthly (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                mes_referencia TEXT,
                qtd_instalacoes_gd INTEGER,
                energia_injetada_total REAL,
                energia_injetada_fora_ponta REAL,
                energia_injetada_ponta REAL,
                disponibilidade_total REAL,
                demanda_geracao_total REAL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO real_transformer_gd_monthly VALUES (
                'A00074',
                'IGU',
                'IGU-01C2',
                '2025-01',
                1,
                500,
                480,
                20,
                1,
                NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE real_customer_status_by_transformer (
                utd TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                codigo_transformador TEXT,
                municipio TEXT,
                qtd_uc INTEGER,
                qtd_ligado INTEGER,
                qtd_cortado INTEGER,
                qtd_baixado INTEGER
            )
            """
        )
        connection.execute(
            """
            INSERT INTO real_customer_status_by_transformer VALUES (
                'UTD',
                'IGU',
                'IGU-01C2',
                'A00074',
                'RECIFE',
                100,
                80,
                20,
                10
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE real_transformer_notes (
                utd TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                codigo_transformador TEXT,
                municipio TEXT,
                tipo_nota TEXT,
                ano_referencia TEXT,
                quantidade_notas INTEGER
            )
            """
        )
        connection.execute(
            """
            INSERT INTO real_transformer_notes VALUES (
                'UTD',
                'IGU',
                'IGU-01C2',
                'A00074',
                'RECIFE',
                'INSPECAO',
                '2025',
                5
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE real_recovered_energy (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                energia_recuperada_media_kwh REAL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO real_recovered_energy VALUES (
                'A00074',
                'IGU',
                'IGU-01C2',
                1200
            )
            """
        )