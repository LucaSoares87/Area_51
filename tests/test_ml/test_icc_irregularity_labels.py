import csv
import sqlite3
from pathlib import Path

from src.aerial_housing_detection.ml.icc_irregularity_labels import (
    IccIrregularityLabelImporter,
    normalize_icc_row,
)


def test_normalize_icc_row_maps_semicolon_source_columns() -> None:
    row = {
        "QMNUM": "0001",
        "ANLAGE": "0000000570",
        "ZCGACCOUN": "007049148130",
        "COD_IRREG": "101",
        "P_INIIRREG": "2016/09",
        "P_FINIRREG": "2016/11",
        "ERDAT": "20161104",
        "AEDAT": "20161128",
        "CODSIT": "60",
        "ONEORDERNUMBER": "123456",
    }

    normalized = normalize_icc_row(row)

    assert normalized["numero_nota"] == "0001"
    assert normalized["instalacao"] == "0000000570"
    assert normalized["conta_contrato"] == "007049148130"
    assert normalized["codigo_irregularidade"] == "101"
    assert normalized["periodo_inicio_irregularidade"] == "2016-09"
    assert normalized["periodo_fim_irregularidade"] == "2016-11"
    assert normalized["data_criacao"] == "2016-11-04"
    assert normalized["data_atualizacao"] == "2016-11-28"
    assert normalized["codigo_situacao"] == "60"
    assert normalized["numero_ordem"] == "123456"


def test_icc_importer_imports_rows_and_builds_transformer_labels(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "area51.db"
    source_path = tmp_path / "icc.csv"

    _create_real_transformer_customers(db_path)
    _write_icc_source(source_path)

    result = IccIrregularityLabelImporter(
        db_path=db_path,
        source_path=source_path,
    ).run()

    assert result.imported_rows == 3
    assert result.label_rows == 2

    with sqlite3.connect(db_path) as connection:
        irregularity_rows = connection.execute(
            "SELECT COUNT(*) FROM real_icc_active_irregularities"
        ).fetchone()[0]

        label_rows = connection.execute(
            """
            SELECT
                codigo_transformador,
                mes_referencia,
                qtd_irregularidades_ativas,
                qtd_instalacoes_com_irregularidade,
                target_irregularidade_ativa
            FROM real_transformer_irregularity_labels
            ORDER BY codigo_transformador, mes_referencia
            """
        ).fetchall()

    assert irregularity_rows == 3
    assert label_rows == [
        ("TRF-001", "2016-09", 2, 2, 1),
        ("TRF-002", "2017-01", 1, 1, 1),
    ]


def test_icc_importer_handles_missing_source_file(tmp_path: Path) -> None:
    db_path = tmp_path / "area51.db"
    source_path = tmp_path / "missing.csv"

    _create_real_transformer_customers(db_path)

    result = IccIrregularityLabelImporter(
        db_path=db_path,
        source_path=source_path,
    ).run()

    assert result.imported_rows == 0
    assert result.label_rows == 0

    with sqlite3.connect(db_path) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM real_icc_active_irregularities"
        ).fetchone()[0]

    assert count == 0


def test_icc_importer_returns_zero_labels_without_customer_table(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "area51.db"
    source_path = tmp_path / "icc.csv"

    _write_icc_source(source_path)

    result = IccIrregularityLabelImporter(
        db_path=db_path,
        source_path=source_path,
    ).run()

    assert result.imported_rows == 3
    assert result.label_rows == 0


def _create_real_transformer_customers(db_path: Path) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE real_transformer_customers (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                instalacao TEXT,
                conta_contrato TEXT
            )
            """
        )

        connection.executemany(
            """
            INSERT INTO real_transformer_customers (
                codigo_transformador,
                codigo_subestacao,
                codigo_alimentador,
                instalacao,
                conta_contrato
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("TRF-001", "SE-01", "AL-01", "0000000570", "007049148130"),
                ("TRF-001", "SE-01", "AL-01", "0000001191", "000489681013"),
                ("TRF-002", "SE-01", "AL-02", "0000001335", "002321557018"),
            ],
        )


def _write_icc_source(path: Path) -> None:
    rows = [
        {
            "QMNUM": "0001",
            "ANLAGE": "0000000570",
            "VERSAO": "1",
            "VERSAO_ATUAL": "X",
            "TARIFTYP": "B1",
            "ZCGACCOUN": "007049148130",
            "COD_IRREG": "101",
            "ALINEA": "A",
            "P_INIIRREG": "2016/09",
            "P_FINIRREG": "2016/11",
            "AUSBS": "",
            "AEDAT": "20161128",
            "ERDAT": "20161104",
            "RPNUM": "RP001",
            "PRINTDOC": "",
            "PRINTDOC2": "",
            "PRINTDOC3": "",
            "OPBEL": "",
            "OPBEL2": "",
            "OPBEL3": "",
            "STAT_I": "",
            "STATP2": "",
            "CODSIT": "60",
            "RESPI": "",
            "ONEORDERNUMBER": "123456",
        },
        {
            "QMNUM": "0002",
            "ANLAGE": "0000001191",
            "VERSAO": "1",
            "VERSAO_ATUAL": "X",
            "TARIFTYP": "B1",
            "ZCGACCOUN": "000489681013",
            "COD_IRREG": "107",
            "ALINEA": "B",
            "P_INIIRREG": "2016/09",
            "P_FINIRREG": "2016/11",
            "AUSBS": "",
            "AEDAT": "20161128",
            "ERDAT": "20161104",
            "RPNUM": "RP002",
            "PRINTDOC": "",
            "PRINTDOC2": "",
            "PRINTDOC3": "",
            "OPBEL": "",
            "OPBEL2": "",
            "OPBEL3": "",
            "STAT_I": "",
            "STATP2": "",
            "CODSIT": "60",
            "RESPI": "",
            "ONEORDERNUMBER": "789012",
        },
        {
            "QMNUM": "0003",
            "ANLAGE": "0000001335",
            "VERSAO": "1",
            "VERSAO_ATUAL": "X",
            "TARIFTYP": "B1",
            "ZCGACCOUN": "002321557018",
            "COD_IRREG": "400",
            "ALINEA": "",
            "P_INIIRREG": "2017/01",
            "P_FINIRREG": "2017/02",
            "AUSBS": "",
            "AEDAT": "20170210",
            "ERDAT": "20170115",
            "RPNUM": "RP003",
            "PRINTDOC": "",
            "PRINTDOC2": "",
            "PRINTDOC3": "",
            "OPBEL": "",
            "OPBEL2": "",
            "OPBEL3": "",
            "STAT_I": "",
            "STATP2": "",
            "CODSIT": "9",
            "RESPI": "",
            "ONEORDERNUMBER": "345678",
        },
    ]

    fieldnames = list(rows[0].keys())

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
