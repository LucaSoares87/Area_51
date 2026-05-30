import sqlite3
from pathlib import Path

from src.aerial_housing_detection.services.concessionaria_csv_importer import (
    ConcessionariaCsvImporter,
)


def test_concessionaria_csv_importer_imports_core_files(tmp_path: Path) -> None:
    imports_dir = tmp_path / "imports"
    imports_dir.mkdir()

    (imports_dir / "ativos_eletricos.csv").write_text(
        "\ufeff    ;CODIGO_TRANSFORMADOR;CODIGO_SUBESTACAO;"
        "CODIGO_ALIMENTADOR;PG_ID     ;PG     ;CODIGO_PONTO_MEDIDO;"
        "CONTA_CONTRATO;DATA_CADASTRO_GSE  ;DATA_EXCLUSAO;LATITUDE  ;LONGITUDE  \n"
        "1;A00003;IGU;IGU-01C2;1437138.0;S086809;001063526017;"
        "1063526017;2005-01-01 00:00:00;;-7.7543573;-34.8268318\n",
        encoding="utf-8",
    )

    (imports_dir / "consumo_transformador_mensal.csv").write_text(
        "    ;CODIGO_TRANSFORMADOR;CODIGO_SUBESTACAO;CODIGO_ALIMENTADOR;"
        "MES_REFERENCIA;QTD_CLIENTES_COM_CONSUMO;CONSUMO_FATURADO_KWH\n"
        "1;A00003;IGU;IGU-01C2;202501;15;1.479,68\n",
        encoding="utf-8",
    )

    (imports_dir / "gd_transformador_mensal.csv").write_text(
        "    ;CODIGO_TRANSFORMADOR;CODIGO_SUBESTACAO;CODIGO_ALIMENTADOR;"
        "MES_REFERENCIA;QTD_INSTALACOES_GD;ENERGIA_INJETADA_TOTAL;"
        "ENERGIA_INJETADA_FORA_PONTA;ENERGIA_INJETADA_PONTA;"
        "DISPONIBILIDADE_TOTAL;DEMANDA_GERACAO_TOTAL\n"
        "1;A00003;IGU;IGU-01C2;2025-01;1;8.000,06;7.998,55;1,51;1;?\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "area51.db"

    summary = ConcessionariaCsvImporter(
        imports_dir=imports_dir,
        db_path=db_path,
    ).import_all()

    assert len(summary.imported_files) == 3

    with sqlite3.connect(db_path) as connection:
        consumption = connection.execute(
            """
            SELECT consumo_faturado_kwh, mes_referencia
            FROM real_transformer_consumption_monthly
            """
        ).fetchone()

        gd = connection.execute(
            """
            SELECT energia_injetada_total, demanda_geracao_total
            FROM real_transformer_gd_monthly
            """
        ).fetchone()

    assert consumption == (1479.68, "2025-01")
    assert gd == (8000.06, None)
