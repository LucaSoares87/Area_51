import csv
import sqlite3
from pathlib import Path

from src.aerial_housing_detection.ml.synthetic_loss_agent_dataset import (
    SyntheticLossAgentDatasetImporter,
)


def test_synthetic_loss_agent_importer_imports_expected_tables(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "area51.db"
    source_dir = tmp_path / "synthetic_ml"
    source_dir.mkdir()

    _write_synthetic_files(source_dir)

    result = SyntheticLossAgentDatasetImporter(
        db_path=db_path,
        source_dir=source_dir,
    ).run()

    assert result.total_rows == 5
    assert result.imported_tables == {
        "synthetic_loss_agent_dataset": 1,
        "synthetic_transformer_heatmap": 1,
        "synthetic_feeder_heatmap": 1,
        "synthetic_housing_estimates": 1,
        "synthetic_irregularity_labels": 1,
    }

    with sqlite3.connect(db_path) as connection:
        dataset_count = connection.execute(
            "SELECT COUNT(*) FROM synthetic_loss_agent_dataset"
        ).fetchone()[0]

        heatmap_count = connection.execute(
            "SELECT COUNT(*) FROM synthetic_transformer_heatmap"
        ).fetchone()[0]

        feeder_count = connection.execute(
            "SELECT COUNT(*) FROM synthetic_feeder_heatmap"
        ).fetchone()[0]

        housing_count = connection.execute(
            "SELECT COUNT(*) FROM synthetic_housing_estimates"
        ).fetchone()[0]

        labels_count = connection.execute(
            "SELECT COUNT(*) FROM synthetic_irregularity_labels"
        ).fetchone()[0]

    assert dataset_count == 1
    assert heatmap_count == 1
    assert feeder_count == 1
    assert housing_count == 1
    assert labels_count == 1


def test_synthetic_loss_agent_importer_handles_missing_files(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "area51.db"
    source_dir = tmp_path / "synthetic_ml"
    source_dir.mkdir()

    result = SyntheticLossAgentDatasetImporter(
        db_path=db_path,
        source_dir=source_dir,
    ).run()

    assert result.total_rows == 0
    assert result.imported_tables == {
        "synthetic_loss_agent_dataset": 0,
        "synthetic_transformer_heatmap": 0,
        "synthetic_feeder_heatmap": 0,
        "synthetic_housing_estimates": 0,
        "synthetic_irregularity_labels": 0,
    }


def test_synthetic_loss_agent_importer_replaces_previous_rows(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "area51.db"
    source_dir = tmp_path / "synthetic_ml"
    source_dir.mkdir()

    _write_synthetic_files(source_dir)

    importer = SyntheticLossAgentDatasetImporter(
        db_path=db_path,
        source_dir=source_dir,
    )

    first_result = importer.run()
    second_result = importer.run()

    assert first_result.total_rows == 5
    assert second_result.total_rows == 5

    with sqlite3.connect(db_path) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM synthetic_loss_agent_dataset"
        ).fetchone()[0]

    assert count == 1


def _write_synthetic_files(source_dir: Path) -> None:
    _write_csv(
        source_dir / "fake_dataset_agente_perdas_transformador_mes.csv",
        [
            {
                "codigo_transformador": "TRF-001",
                "codigo_subestacao": "SE-01",
                "codigo_alimentador": "AL-01",
                "mes_referencia": "2025-01",
                "latitude": "-8.001",
                "longitude": "-34.901",
                "qtd_clientes_vinculados": "120",
                "qtd_clientes_com_consumo": "118",
                "consumo_faturado_kwh": "15000.5",
                "qtd_instalacoes_gd": "2",
                "energia_injetada_total": "500.2",
                "qtd_inspecoes": "4",
                "qtd_irregularidades_confirmadas": "2",
                "qtd_defeitos_concessionaria": "1",
                "qtd_sem_perdas": "1",
                "qtd_normais": "0",
                "qtd_casas_cras": "130",
                "qtd_casas_ibge": "125",
                "qtd_casas_telhado": "140",
                "media_estimativa_casas": "131.6",
                "divergencia_casas_clientes": "11.6",
                "nivel_divergencia_habitacional": "MEDIA_DIVERGENCIA",
                "perda_estimada_kwh": "2300.5",
                "perda_estimada_percentual": "0.153",
                "nivel_calor": "ALTO",
                "target_irregularidade_confirmada": "1",
                "prioridade_ml_operacional": "ALTA",
            }
        ],
    )

    _write_csv(
        source_dir / "fake_heatmap_transformador_mes.csv",
        [
            {
                "codigo_transformador": "TRF-001",
                "codigo_subestacao": "SE-01",
                "codigo_alimentador": "AL-01",
                "mes_referencia": "2025-01",
                "latitude": "-8.001",
                "longitude": "-34.901",
                "consumo_faturado_kwh": "15000.5",
                "energia_injetada_total": "500.2",
                "perda_estimada_kwh": "2300.5",
                "perda_estimada_percentual": "0.153",
                "qtd_irregularidades_confirmadas": "2",
                "target_irregularidade_confirmada": "1",
                "nivel_calor": "ALTO",
            }
        ],
    )

    _write_csv(
        source_dir / "fake_heatmap_alimentador_mes.csv",
        [
            {
                "codigo_subestacao": "SE-01",
                "codigo_alimentador": "AL-01",
                "mes_referencia": "2025-01",
                "qtd_transformadores": "5",
                "latitude_centroide": "-8.002",
                "longitude_centroide": "-34.902",
                "consumo_faturado_kwh": "80000",
                "perda_estimada_kwh": "10000",
                "perda_estimada_percentual_media": "0.12",
                "qtd_irregularidades_confirmadas": "8",
                "nivel_calor_alimentador": "ALTO",
            }
        ],
    )

    _write_csv(
        source_dir / "fake_estimativa_casas_transformador.csv",
        [
            {
                "codigo_transformador": "TRF-001",
                "codigo_subestacao": "SE-01",
                "codigo_alimentador": "AL-01",
                "latitude": "-8.001",
                "longitude": "-34.901",
                "qtd_clientes_cadastrados": "120",
                "qtd_casas_cras": "130",
                "qtd_casas_ibge": "125",
                "qtd_casas_telhado": "140",
                "media_estimativa_casas": "131.6",
                "divergencia_casas_clientes": "11.6",
                "nivel_divergencia_habitacional": "MEDIA_DIVERGENCIA",
            }
        ],
    )

    _write_csv(
        source_dir / "fake_labels_irregularidade_transformador_mes.csv",
        [
            {
                "codigo_transformador": "TRF-001",
                "codigo_subestacao": "SE-01",
                "codigo_alimentador": "AL-01",
                "mes_referencia": "2025-01",
                "qtd_inspecoes": "4",
                "qtd_instalacoes_inspecionadas": "3",
                "qtd_irregularidades_confirmadas": "2",
                "qtd_defeitos_concessionaria": "1",
                "qtd_sem_perdas": "1",
                "qtd_normais": "0",
                "target_irregularidade_confirmada": "1",
            }
        ],
    )


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(rows[0].keys())

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
