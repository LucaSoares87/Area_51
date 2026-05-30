import sqlite3
from pathlib import Path

from src.aerial_housing_detection.services.concessionaria_real_analysis import (
    ConcessionariaRealAnalysisService,
    RealConcessionariaAnalysisRequest,
)


def test_real_analysis_returns_transformer_indicators(tmp_path: Path) -> None:
    db_path = tmp_path / "area51.db"
    _create_test_database(db_path)

    service = ConcessionariaRealAnalysisService(db_path=db_path)

    result = service.analyze(
        RealConcessionariaAnalysisRequest(transformer_code="A00003")
    )

    assert result["found"] is True
    assert result["asset"]["codigo_transformador"] == "A00003"
    assert result["consumption"]["consumo_faturado_kwh"] == 24000
    assert result["customer_status"]["qtd_ligado"] == 80
    assert result["indicators"]["consumo_medio_por_cliente_ligado"] == 300
    assert result["indicators"]["prioridade"] in {"Baixa", "Média", "Alta"}


def test_real_analysis_finds_nearest_transformer_by_coordinates(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "area51.db"
    _create_test_database(db_path)

    service = ConcessionariaRealAnalysisService(db_path=db_path)

    result = service.analyze(
        RealConcessionariaAnalysisRequest(
            latitude=-7.7543,
            longitude=-34.8268,
        )
    )

    assert result["found"] is True
    assert result["asset"]["codigo_transformador"] == "A00003"


def _create_test_database(db_path: Path) -> None:
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
                'A00003',
                'IGU',
                'IGU-01C2',
                1437138.0,
                'S086809',
                '001063526017',
                '1063526017',
                '2005-01-01',
                NULL,
                -7.7543573,
                -34.8268318
            )
            """
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
                'A00003',
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
                'A00003',
                'IGU',
                'IGU-01C2',
                '2025-01',
                1,
                8000,
                7998,
                2,
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
                'A00003',
                'RECIFE',
                100,
                80,
                12,
                8
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
                'A00003',
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
                'A00003',
                'IGU',
                'IGU-01C2',
                1200
            )
            """
        )
