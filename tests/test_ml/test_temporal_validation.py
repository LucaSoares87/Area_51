import json
from pathlib import Path

from src.aerial_housing_detection.ml.temporal_validation import (
    TransformerTemporalValidator,
)


def test_temporal_validator_generates_monthly_metrics(tmp_path: Path) -> None:
    dataset_path = tmp_path / "ml_transformer_dataset.csv"
    output_path = tmp_path / "ml_temporal_validation_metrics.json"

    dataset_path.write_text(
        "\n".join(
            [
                "codigo_transformador,mes_referencia,risco_score,"
                "consumo_faturado_kwh,target_risco_alto",
                "A00001,2025-01,90,10000,1",
                "A00002,2025-01,10,1000,0",
                "A00003,2025-02,80,9000,1",
                "A00004,2025-02,20,2000,0",
            ]
        ),
        encoding="utf-8",
    )

    result = TransformerTemporalValidator(
        dataset_path=dataset_path,
        output_path=output_path,
    ).run()

    assert result.total_rows == 4
    assert result.total_months == 2
    assert result.months == ["2025-01", "2025-02"]

    metrics = json.loads(output_path.read_text(encoding="utf-8"))

    assert metrics["total_rows"] == 4
    assert metrics["total_months"] == 2
    assert metrics["positive_rows"] == 2
    assert metrics["global_precision_at_10"] == 0.5
    assert metrics["global_recall_at_50"] == 1.0
    assert metrics["months"]["2025-01"]["positive_rows"] == 1
    assert metrics["months"]["2025-02"]["positive_rows"] == 1


def test_temporal_validator_creates_fallback_target_when_missing_positive_class(
    tmp_path: Path,
) -> None:
    dataset_path = tmp_path / "ml_transformer_dataset.csv"
    output_path = tmp_path / "ml_temporal_validation_metrics.json"

    lines = [
        "codigo_transformador,mes_referencia,risco_score,"
        "consumo_faturado_kwh,target_risco_alto"
    ]

    for index in range(10):
        lines.append(f"A0000{index},2025-01,0,{index * 1000},0")

    dataset_path.write_text("\n".join(lines), encoding="utf-8")

    result = TransformerTemporalValidator(
        dataset_path=dataset_path,
        output_path=output_path,
    ).run()

    metrics = json.loads(output_path.read_text(encoding="utf-8"))

    assert result.total_rows == 10
    assert result.total_months == 1
    assert metrics["positive_rows"] == 1
    assert metrics["positive_rate"] == 0.1
    assert metrics["global_precision_at_10"] == 0.1
    assert metrics["global_recall_at_50"] == 1.0


def test_temporal_validator_handles_missing_dataset(tmp_path: Path) -> None:
    dataset_path = tmp_path / "missing.csv"
    output_path = tmp_path / "ml_temporal_validation_metrics.json"

    result = TransformerTemporalValidator(
        dataset_path=dataset_path,
        output_path=output_path,
    ).run()

    metrics = json.loads(output_path.read_text(encoding="utf-8"))

    assert result.total_rows == 0
    assert result.total_months == 0
    assert result.months == []
    assert metrics["total_rows"] == 0
    assert metrics["total_months"] == 0
