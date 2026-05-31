import csv
import json
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any

DATASET_PATH = Path("data/processed/ml_transformer_dataset.csv")
METRICS_PATH = Path("reports/ml_baseline_metrics.json")
RANKING_PATH = Path("reports/ml_baseline_ranking.csv")


@dataclass(frozen=True)
class MlBaselineResult:
    dataset_path: str
    metrics_path: str
    ranking_path: str
    total_rows: int
    positive_rows: int
    precision_at_10: float
    precision_at_50: float
    recall_at_50: float


class TransformerMlBaselineModel:
    def __init__(
        self,
        dataset_path: Path = DATASET_PATH,
        metrics_path: Path = METRICS_PATH,
        ranking_path: Path = RANKING_PATH,
    ) -> None:
        self.dataset_path = dataset_path
        self.metrics_path = metrics_path
        self.ranking_path = ranking_path

    def run(self) -> MlBaselineResult:
        rows = self._read_dataset()
        rows = self._ensure_target_has_positive_class(rows)

        ranked_rows = sorted(
            rows,
            key=lambda row: (
                _to_float(row.get("risco_score")),
                _to_float(row.get("consumo_faturado_kwh")),
            ),
            reverse=True,
        )

        metrics = self._compute_metrics(ranked_rows)

        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        self.ranking_path.parent.mkdir(parents=True, exist_ok=True)

        self.metrics_path.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        self.ranking_path.write_text(
            self._to_ranking_csv(ranked_rows),
            encoding="utf-8",
        )

        return MlBaselineResult(
            dataset_path=str(self.dataset_path),
            metrics_path=str(self.metrics_path),
            ranking_path=str(self.ranking_path),
            total_rows=int(metrics["total_rows"]),
            positive_rows=int(metrics["positive_rows"]),
            precision_at_10=float(metrics["precision_at_10"]),
            precision_at_50=float(metrics["precision_at_50"]),
            recall_at_50=float(metrics["recall_at_50"]),
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

    def _compute_metrics(self, ranked_rows: list[dict[str, Any]]) -> dict[str, Any]:
        total_rows = len(ranked_rows)
        positive_rows = sum(_to_int(row.get("target_risco_alto")) for row in ranked_rows)

        precision_at_10 = _precision_at_k(ranked_rows, 10)
        precision_at_50 = _precision_at_k(ranked_rows, 50)
        recall_at_50 = _recall_at_k(ranked_rows, 50, positive_rows)

        return {
            "model_name": "score_baseline",
            "model_type": "ranking_baseline",
            "target": "target_risco_alto",
            "score_column": "risco_score",
            "fallback_target": positive_rows > 0,
            "fallback_strategy": (
                "top_10_percent_consumo_faturado_kwh_when_no_positive_target"
            ),
            "total_rows": total_rows,
            "positive_rows": positive_rows,
            "positive_rate": _safe_divide(positive_rows, total_rows),
            "precision_at_10": precision_at_10,
            "precision_at_50": precision_at_50,
            "recall_at_50": recall_at_50,
            "notes": (
                "Baseline inicial usando risco_score como pontuação principal "
                "e consumo_faturado_kwh como desempate. Quando o alvo proxy "
                "vem sem classe positiva, o pipeline cria positivos a partir "
                "dos 10% maiores consumos faturados. Esse alvo ainda não "
                "representa irregularidade confirmada em campo."
            ),
        }

    def _to_ranking_csv(self, ranked_rows: list[dict[str, Any]]) -> str:
        output_columns = [
            "rank",
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

        lines: list[dict[str, Any]] = []

        for index, row in enumerate(ranked_rows, start=1):
            output = {column: row.get(column, "") for column in output_columns}
            output["rank"] = index
            lines.append(output)

        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=output_columns)
        writer.writeheader()
        writer.writerows(lines)

        return buffer.getvalue()


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
