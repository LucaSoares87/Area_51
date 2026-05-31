import csv
import json
from pathlib import Path

from src.aerial_housing_detection.ml.baseline_model import (
    TransformerMlBaselineModel,
)


def test_baseline_model_generates_metrics_and_ranking(tmp_path: Path) -> None:
    dataset_path = tmp_path / "ml_transformer_dataset.csv"
    metrics_path = tmp_path / "ml_baseline_metrics.json"
    ranking_path = tmp_path / "ml_baseline_ranking.csv"

    _write_dataset(dataset_path)

    result = TransformerMlBaselineModel(
        dataset_path=dataset_path,
        metrics_path=metrics_path,
        ranking_path=ranking_path,
    ).run()

    assert result.total_rows == 4
    assert result.positive_rows == 2
    assert result.precision_at_10 == 0.5
    assert result.precision_at_50 == 0.5
    assert result.recall_at_50 == 1.0

    assert metrics_path.exists()
    assert ranking_path.exists()

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))

    assert metrics["total_rows"] == 4
    assert metrics["positive_rows"] == 2
    assert metrics["model_name"] == "score_baseline"


def test_baseline_model_creates_fallback_target_when_no_positive_class(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "ml_transformer_dataset.csv"
    metrics_path = tmp_path / "ml_baseline_metrics.json"
    ranking_path = tmp_path / "ml_baseline_ranking.csv"

    _write_dataset_without_positive_target(dataset_path)

    result = TransformerMlBaselineModel(
        dataset_path=dataset_path,
        metrics_path=metrics_path,
        ranking_path=ranking_path,
    ).run()

    assert result.total_rows == 10
    assert result.positive_rows == 1
    assert result.precision_at_10 == 0.1
    assert result.recall_at_50 == 1.0

    ranking_rows = list(
        csv.DictReader(ranking_path.open("r", encoding="utf-8"))
    )

    positive_rows = [
        row for row in ranking_rows if row["target_risco_alto"] == "1"
    ]

    assert len(positive_rows) == 1
    assert positive_rows[0]["codigo_transformador"] == "A00009"


def test_baseline_model_handles_missing_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "missing.csv"
    metrics_path = tmp_path / "ml_baseline_metrics.json"
    ranking_path = tmp_path / "ml_baseline_ranking.csv"

    result = TransformerMlBaselineModel(
        dataset_path=dataset_path,
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


def _write_dataset(path: Path) -> None:
    rows = [
        {
            "codigo_transformador": "A00001",
            "codigo_subestacao": "SE",
            "codigo_alimentador": "AL",
            "mes_referencia": "2025-01",
            "risco_score": "90",
            "prioridade": "Alta",
            "target_risco_alto": "1",
            "consumo_faturado_kwh": "10000",
            "qtd_ligado": "80",
            "qtd_cortado": "10",
            "qtd_baixado": "2",
            "energia_injetada_total": "0",
            "qtd_notas": "5",
            "energia_recuperada_media_kwh": "0",
        },
        {
            "codigo_transformador": "A00002",
            "codigo_subestacao": "SE",
            "codigo_alimentador": "AL",
            "mes_referencia": "2025-01",
            "risco_score": "80",
            "prioridade": "Alta",
            "target_risco_alto": "1",
            "consumo_faturado_kwh": "8000",
            "qtd_ligado": "70",
            "qtd_cortado": "8",
            "qtd_baixado": "1",
            "energia_injetada_total": "0",
            "qtd_notas": "4",
            "energia_recuperada_media_kwh": "0",
        },
        {
            "codigo_transformador": "A00003",
            "codigo_subestacao": "SE",
            "codigo_alimentador": "AL",
            "mes_referencia": "2025-01",
            "risco_score": "20",
            "prioridade": "Baixa",
            "target_risco_alto": "0",
            "consumo_faturado_kwh": "2000",
            "qtd_ligado": "20",
            "qtd_cortado": "1",
            "qtd_baixado": "0",
            "energia_injetada_total": "0",
            "qtd_notas": "0",
            "energia_recuperada_media_kwh": "0",
        },
        {
            "codigo_transformador": "A00004",
            "codigo_subestacao": "SE",
            "codigo_alimentador": "AL",
            "mes_referencia": "2025-01",
            "risco_score": "10",
            "prioridade": "Baixa",
            "target_risco_alto": "0",
            "consumo_faturado_kwh": "1000",
            "qtd_ligado": "10",
            "qtd_cortado": "0",
            "qtd_baixado": "0",
            "energia_injetada_total": "0",
            "qtd_notas": "0",
            "energia_recuperada_media_kwh": "0",
        },
    ]

    _write_rows(path, rows)


def _write_dataset_without_positive_target(path: Path) -> None:
    rows = []

    for index in range(10):
        rows.append(
            {
                "codigo_transformador": f"A0000{index}",
                "codigo_subestacao": "SE",
                "codigo_alimentador": "AL",
                "mes_referencia": "2025-01",
                "risco_score": "0",
                "prioridade": "Baixa",
                "target_risco_alto": "0",
                "consumo_faturado_kwh": str(index * 1000),
                "qtd_ligado": "0",
                "qtd_cortado": "0",
                "qtd_baixado": "0",
                "energia_injetada_total": "0",
                "qtd_notas": "0",
                "energia_recuperada_media_kwh": "0",
            }
        )

    _write_rows(path, rows)


def _write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "codigo_transformador",
        "codigo_subestacao",
        "codigo_alimentador",
        "mes_referencia",
        "risco_score",
        "prioridade",
        "target_risco_alto",
        "consumo_faturado_kwh",
        "qtd_ligado",
        "qtd_cortado",
        "qtd_baixado",
        "energia_injetada_total",
        "qtd_notas",
        "energia_recuperada_media_kwh",
    ]

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
