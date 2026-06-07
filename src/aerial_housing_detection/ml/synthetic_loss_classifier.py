import csv
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path("data/area51.db")
METRICS_PATH = Path("reports/synthetic_loss_classifier_metrics.json")
RANKING_PATH = Path("reports/synthetic_loss_classifier_ranking.csv")


@dataclass(frozen=True)
class SyntheticLossClassifierResult:
    database_path: str
    metrics_path: str
    ranking_path: str
    total_rows: int
    positive_rows: int
    precision_at_10: float
    precision_at_50: float
    recall_at_50: float


class SyntheticLossClassifier:
    def __init__(
        self,
        db_path: Path = DB_PATH,
        metrics_path: Path = METRICS_PATH,
        ranking_path: Path = RANKING_PATH,
    ) -> None:
        self.db_path = db_path
        self.metrics_path = metrics_path
        self.ranking_path = ranking_path

    def run(self) -> SyntheticLossClassifierResult:
        rows = self._read_rows()
        scored_rows = [score_synthetic_loss_row(row) for row in rows]
        ranked_rows = sorted(
            scored_rows,
            key=lambda row: (
                row["loss_probability"],
                row["perda_estimada_kwh"],
                row["qtd_irregularidades_confirmadas"],
            ),
            reverse=True,
        )

        metrics = build_synthetic_loss_metrics(ranked_rows)

        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        self.ranking_path.parent.mkdir(parents=True, exist_ok=True)

        self.metrics_path.write_text(
            json.dumps(metrics, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.ranking_path.write_text(
            _to_csv(ranked_rows),
            encoding="utf-8",
        )

        return SyntheticLossClassifierResult(
            database_path=str(self.db_path),
            metrics_path=str(self.metrics_path),
            ranking_path=str(self.ranking_path),
            total_rows=int(metrics["total_rows"]),
            positive_rows=int(metrics["positive_rows"]),
            precision_at_10=float(metrics["precision_at_10"]),
            precision_at_50=float(metrics["precision_at_50"]),
            recall_at_50=float(metrics["recall_at_50"]),
        )

    def _read_rows(self) -> list[dict[str, Any]]:
        if not self.db_path.exists():
            return []

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row

            if not _table_exists(connection, "synthetic_loss_agent_dataset"):
                return []

            rows = connection.execute(
                """
                SELECT
                    codigo_transformador,
                    codigo_subestacao,
                    codigo_alimentador,
                    mes_referencia,
                    latitude,
                    longitude,
                    qtd_clientes_vinculados,
                    qtd_clientes_com_consumo,
                    consumo_faturado_kwh,
                    qtd_instalacoes_gd,
                    energia_injetada_total,
                    qtd_inspecoes,
                    qtd_irregularidades_confirmadas,
                    qtd_defeitos_concessionaria,
                    qtd_sem_perdas,
                    qtd_normais,
                    qtd_casas_cras,
                    qtd_casas_ibge,
                    qtd_casas_telhado,
                    media_estimativa_casas,
                    divergencia_casas_clientes,
                    nivel_divergencia_habitacional,
                    perda_estimada_kwh,
                    perda_estimada_percentual,
                    nivel_calor,
                    target_irregularidade_confirmada,
                    prioridade_ml_operacional
                FROM synthetic_loss_agent_dataset
                """
            ).fetchall()

            return [dict(row) for row in rows]


def score_synthetic_loss_row(row: dict[str, Any]) -> dict[str, Any]:
    perda_percentual = _to_float(row.get("perda_estimada_percentual"))
    perda_kwh = _to_float(row.get("perda_estimada_kwh"))
    consumo = _to_float(row.get("consumo_faturado_kwh"))
    irregularidades = _to_float(row.get("qtd_irregularidades_confirmadas"))
    divergencia = _to_float(row.get("divergencia_casas_clientes"))
    gd = _to_float(row.get("energia_injetada_total"))
    inspecoes = _to_float(row.get("qtd_inspecoes"))

    score = 0.0
    score += min(perda_percentual / 0.35, 1.0) * 0.30
    score += min(perda_kwh / 7000.0, 1.0) * 0.20
    score += min(irregularidades / 5.0, 1.0) * 0.20
    score += min(max(divergencia, 0.0) / 60.0, 1.0) * 0.15
    score += min(consumo / 30000.0, 1.0) * 0.10
    score += min(gd / 4000.0, 1.0) * 0.03
    score += min(inspecoes / 8.0, 1.0) * 0.02

    probability = max(0.0, min(score, 1.0))

    enriched = dict(row)
    enriched["loss_probability"] = round(probability, 6)
    enriched["predicted_irregularity"] = 1 if probability >= 0.50 else 0
    enriched["model_name"] = "synthetic_rule_based_loss_classifier"
    enriched["model_stage"] = "synthetic_supervised_baseline"

    return enriched


def build_synthetic_loss_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_rows = len(rows)
    positive_rows = sum(
        _to_int(row.get("target_irregularidade_confirmada")) for row in rows
    )

    return {
        "model_name": "synthetic_rule_based_loss_classifier",
        "model_stage": "synthetic_supervised_baseline",
        "total_rows": total_rows,
        "positive_rows": positive_rows,
        "positive_rate": round(positive_rows / total_rows, 6) if total_rows else 0.0,
        "precision_at_10": precision_at_k(rows, 10),
        "precision_at_50": precision_at_k(rows, 50),
        "recall_at_50": recall_at_k(rows, 50),
        "notes": (
            "Classificador sintético baseado em regras ponderadas. "
            "Usa target_irregularidade_confirmada de dados sintéticos."
        ),
    }


def precision_at_k(rows: list[dict[str, Any]], k: int) -> float:
    if not rows or k <= 0:
        return 0.0

    top_rows = rows[:k]
    positives = sum(
        _to_int(row.get("target_irregularidade_confirmada")) for row in top_rows
    )

    return round(positives / len(top_rows), 6)


def recall_at_k(rows: list[dict[str, Any]], k: int) -> float:
    if not rows or k <= 0:
        return 0.0

    total_positives = sum(
        _to_int(row.get("target_irregularidade_confirmada")) for row in rows
    )

    if total_positives == 0:
        return 0.0

    top_rows = rows[:k]
    positives_in_top = sum(
        _to_int(row.get("target_irregularidade_confirmada")) for row in top_rows
    )

    return round(positives_in_top / total_positives, 6)


def _to_csv(rows: list[dict[str, Any]]) -> str:
    fieldnames = [
        "codigo_transformador",
        "codigo_subestacao",
        "codigo_alimentador",
        "mes_referencia",
        "latitude",
        "longitude",
        "consumo_faturado_kwh",
        "energia_injetada_total",
        "perda_estimada_kwh",
        "perda_estimada_percentual",
        "qtd_irregularidades_confirmadas",
        "qtd_defeitos_concessionaria",
        "qtd_sem_perdas",
        "qtd_normais",
        "qtd_casas_cras",
        "qtd_casas_ibge",
        "qtd_casas_telhado",
        "media_estimativa_casas",
        "divergencia_casas_clientes",
        "nivel_divergencia_habitacional",
        "nivel_calor",
        "target_irregularidade_confirmada",
        "predicted_irregularity",
        "loss_probability",
        "prioridade_ml_operacional",
        "model_name",
        "model_stage",
    ]

    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fieldnames})

    return buffer.getvalue()


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    ).fetchone()

    return row is not None


def _to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0

    return float(value)


def _to_int(value: Any) -> int:
    if value in (None, ""):
        return 0

    return int(float(value))
