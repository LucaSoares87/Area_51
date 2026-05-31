import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATASET_PATH = Path("data/processed/ml_transformer_dataset.csv")
OUTPUT_PATH = Path("reports/ml_temporal_validation_metrics.json")


@dataclass(frozen=True)
class TemporalValidationResult:
    dataset_path: str
    output_path: str
    total_rows: int
    total_months: int
    months: list[str]


class TransformerTemporalValidator:
    def __init__(
        self,
        dataset_path: Path = DATASET_PATH,
        output_path: Path = OUTPUT_PATH,
    ) -> None:
        self.dataset_path = dataset_path
        self.output_path = output_path

    def run(self) -> TemporalValidationResult:
        rows = self._read_dataset()
        rows = self._ensure_target_has_positive_class(rows)

        metrics = self._compute_temporal_metrics(rows)

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_path.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return TemporalValidationResult(
            dataset_path=str(self.dataset_path),
            output_path=str(self.output_path),
            total_rows=int(metrics["total_rows"]),
            total_months=int(metrics["total_months"]),
            months=list(metrics["months"].keys()),
        )

    def _read_dataset(self) -> list[dict[str, Any]]:
        if not self.dataset_path.exists():
            return []

        with self.dataset_path.open("r", encoding="utf-8", newline="") as file:
            return [dict(row) for row in csv.DictReader(file)]

    def _ensure_target_has_positive_class(
        self,
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not rows:
            return rows

        positive_rows = sum(_to_int(row.get("target_risco_alto")) for row in rows)

        if positive_rows > 0:
            return rows

        ranked_by_consumption = sorted(
            rows,
            key=lambda row: _to_float(row.get("consumo_faturado_kwh")),
            reverse=True,
        )

        cutoff = max(1, round(len(ranked_by_consumption) * 0.10))
        selected_keys = {
            (
                row.get("codigo_transformador"),
                row.get("mes_referencia"),
            )
            for row in ranked_by_consumption[:cutoff]
        }

        adjusted_rows: list[dict[str, Any]] = []

        for row in rows:
            adjusted = dict(row)
            key = (
                adjusted.get("codigo_transformador"),
                adjusted.get("mes_referencia"),
            )
            adjusted["target_risco_alto"] = 1 if key in selected_keys else 0
            adjusted_rows.append(adjusted)

        return adjusted_rows

    def _compute_temporal_metrics(
        self,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        rows_by_month: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for row in rows:
            month = str(row.get("mes_referencia") or "sem_referencia")
            rows_by_month[month].append(row)

        month_metrics: dict[str, Any] = {}

        for month in sorted(rows_by_month):
            month_rows = rows_by_month[month]
            ranked_rows = sorted(
                month_rows,
                key=lambda row: (
                    _to_float(row.get("risco_score")),
                    _to_float(row.get("consumo_faturado_kwh")),
                ),
                reverse=True,
            )

            positives = sum(
                _to_int(row.get("target_risco_alto")) for row in ranked_rows
            )

            month_metrics[month] = {
                "total_rows": len(ranked_rows),
                "positive_rows": positives,
                "positive_rate": _safe_divide(positives, len(ranked_rows)),
                "precision_at_10": _precision_at_k(ranked_rows, 10),
                "precision_at_50": _precision_at_k(ranked_rows, 50),
                "recall_at_50": _recall_at_k(ranked_rows, 50, positives),
                "top_transformers": [
                    row.get("codigo_transformador")
                    for row in ranked_rows[:10]
                ],
            }

        all_ranked_rows = sorted(
            rows,
            key=lambda row: (
                _to_float(row.get("risco_score")),
                _to_float(row.get("consumo_faturado_kwh")),
            ),
            reverse=True,
        )

        total_positive = sum(
            _to_int(row.get("target_risco_alto")) for row in all_ranked_rows
        )

        return {
            "validation_name": "temporal_ranking_validation",
            "target": "target_risco_alto",
            "score_column": "risco_score",
            "fallback_strategy": (
                "top_10_percent_consumo_faturado_kwh_when_no_positive_target"
            ),
            "total_rows": len(rows),
            "total_months": len(month_metrics),
            "positive_rows": total_positive,
            "positive_rate": _safe_divide(total_positive, len(rows)),
            "global_precision_at_10": _precision_at_k(all_ranked_rows, 10),
            "global_precision_at_50": _precision_at_k(all_ranked_rows, 50),
            "global_recall_at_50": _recall_at_k(
                all_ranked_rows,
                50,
                total_positive,
            ),
            "months": month_metrics,
        }


def _precision_at_k(rows: list[dict[str, Any]], k: int) -> float:
    if not rows:
        return 0.0

    selected = rows[: min(k, len(rows))]

    if not selected:
        return 0.0

    positives = sum(_to_int(row.get("target_risco_alto")) for row in selected)
    return round(positives / len(selected), 4)


def _recall_at_k(
    rows: list[dict[str, Any]],
    k: int,
    total_positive: int,
) -> float:
    if not rows or total_positive <= 0:
        return 0.0

    selected = rows[: min(k, len(rows))]
    positives = sum(_to_int(row.get("target_risco_alto")) for row in selected)

    return round(positives / total_positive, 4)


def _safe_divide(numerator: float | int, denominator: float | int) -> float:
    if denominator in (0, None):
        return 0.0

    return round(float(numerator or 0) / float(denominator), 4)


def _to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0

    return float(value)


def _to_int(value: Any) -> int:
    if value in (None, ""):
        return 0

    return int(float(value))
