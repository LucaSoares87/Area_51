import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DATASET_PATH = Path("data/processed/ml_transformer_dataset.csv")
SUMMARY_PATH = Path("reports/ml_explainability_summary.json")
RANKING_PATH = Path("reports/ml_explainability_ranking.csv")


@dataclass(frozen=True)
class ExplainabilityResult:
    dataset_path: str
    summary_path: str
    ranking_path: str
    total_rows: int
    explained_rows: int


class TransformerRankingExplainer:
    def __init__(
        self,
        dataset_path: Path = DATASET_PATH,
        summary_path: Path = SUMMARY_PATH,
        ranking_path: Path = RANKING_PATH,
    ) -> None:
        self.dataset_path = dataset_path
        self.summary_path = summary_path
        self.ranking_path = ranking_path

    def run(self) -> ExplainabilityResult:
        rows = self._read_dataset()
        ranked_rows = self._rank_rows(rows)
        explained_rows = [self._explain_row(row, index) for index, row in enumerate(ranked_rows, start=1)]

        self.summary_path.parent.mkdir(parents=True, exist_ok=True)
        self.ranking_path.parent.mkdir(parents=True, exist_ok=True)

        summary = self._build_summary(explained_rows)

        self.summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.ranking_path.write_text(
            self._to_csv(explained_rows),
            encoding="utf-8",
        )

        return ExplainabilityResult(
            dataset_path=str(self.dataset_path),
            summary_path=str(self.summary_path),
            ranking_path=str(self.ranking_path),
            total_rows=len(rows),
            explained_rows=len(explained_rows),
        )

    def _read_dataset(self) -> list[dict[str, Any]]:
        if not self.dataset_path.exists():
            return []

        with self.dataset_path.open("r", encoding="utf-8", newline="") as file:
            return [dict(row) for row in csv.DictReader(file)]

    def _rank_rows(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(
            rows,
            key=lambda row: (
                _to_float(row.get("target_risco_alto")),
                _to_float(row.get("risco_score")),
                _to_float(row.get("consumo_faturado_kwh")),
            ),
            reverse=True,
        )

    def _explain_row(self, row: dict[str, Any], rank: int) -> dict[str, Any]:
        reasons = build_ranking_reasons(row)

        return {
            "rank": rank,
            "codigo_transformador": row.get("codigo_transformador", ""),
            "codigo_subestacao": row.get("codigo_subestacao", ""),
            "codigo_alimentador": row.get("codigo_alimentador", ""),
            "mes_referencia": row.get("mes_referencia", ""),
            "risco_score": _to_float(row.get("risco_score")),
            "prioridade": row.get("prioridade", ""),
            "target_risco_alto": _to_int(row.get("target_risco_alto")),
            "consumo_faturado_kwh": _to_float(row.get("consumo_faturado_kwh")),
            "consumo_medio_por_cliente_ligado": _to_float(
                row.get("consumo_medio_por_cliente_ligado")
            ),
            "qtd_ligado": _to_int(row.get("qtd_ligado")),
            "qtd_cortado": _to_int(row.get("qtd_cortado")),
            "qtd_baixado": _to_int(row.get("qtd_baixado")),
            "percentual_cortado": _to_float(row.get("percentual_cortado")),
            "percentual_baixado": _to_float(row.get("percentual_baixado")),
            "energia_injetada_total": _to_float(row.get("energia_injetada_total")),
            "qtd_notas": _to_int(row.get("qtd_notas")),
            "energia_recuperada_media_kwh": _to_float(
                row.get("energia_recuperada_media_kwh")
            ),
            "motivos_ranking": "; ".join(reasons),
        }

    def _build_summary(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        reason_counts: dict[str, int] = {}

        for row in rows:
            reasons = str(row.get("motivos_ranking") or "").split("; ")
            for reason in reasons:
                if not reason:
                    continue
                reason_counts[reason] = reason_counts.get(reason, 0) + 1

        top_reasons = sorted(
            reason_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        return {
            "explainability_name": "rule_based_ranking_explainability",
            "total_rows": len(rows),
            "top_10_transformers": [
                {
                    "rank": row["rank"],
                    "codigo_transformador": row["codigo_transformador"],
                    "mes_referencia": row["mes_referencia"],
                    "motivos_ranking": row["motivos_ranking"],
                }
                for row in rows[:10]
            ],
            "reason_counts": dict(top_reasons),
            "notes": (
                "Explicabilidade inicial baseada em regras auditáveis. "
                "Ainda não utiliza SHAP ou explicabilidade de modelo treinado."
            ),
        }

    def _to_csv(self, rows: list[dict[str, Any]]) -> str:
        fieldnames = [
            "rank",
            "codigo_transformador",
            "codigo_subestacao",
            "codigo_alimentador",
            "mes_referencia",
            "risco_score",
            "prioridade",
            "target_risco_alto",
            "consumo_faturado_kwh",
            "consumo_medio_por_cliente_ligado",
            "qtd_ligado",
            "qtd_cortado",
            "qtd_baixado",
            "percentual_cortado",
            "percentual_baixado",
            "energia_injetada_total",
            "qtd_notas",
            "energia_recuperada_media_kwh",
            "motivos_ranking",
        ]

        from io import StringIO

        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

        return buffer.getvalue()


def build_ranking_reasons(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []

    risco_score = _to_float(row.get("risco_score"))
    consumo = _to_float(row.get("consumo_faturado_kwh"))
    consumo_medio = _to_float(row.get("consumo_medio_por_cliente_ligado"))
    percentual_cortado = _to_float(row.get("percentual_cortado"))
    percentual_baixado = _to_float(row.get("percentual_baixado"))
    gd = _to_float(row.get("energia_injetada_total"))
    notas = _to_int(row.get("qtd_notas"))
    recuperada = _to_float(row.get("energia_recuperada_media_kwh"))
    target = _to_int(row.get("target_risco_alto"))

    if target == 1:
        reasons.append("classificado como risco alto pelo alvo proxy")

    if risco_score >= 70:
        reasons.append("score operacional alto")

    if consumo >= 10000:
        reasons.append("alto consumo faturado no período")
    elif consumo >= 5000:
        reasons.append("consumo faturado relevante no período")

    if consumo_medio >= 350:
        reasons.append("consumo médio por cliente ligado elevado")

    if percentual_cortado >= 0.20:
        reasons.append("percentual de clientes cortados elevado")
    elif percentual_cortado >= 0.10:
        reasons.append("percentual de clientes cortados moderado")

    if percentual_baixado >= 0.10:
        reasons.append("percentual de clientes baixados relevante")

    if gd > 0:
        reasons.append("presença de geração distribuída associada")

    if notas >= 10:
        reasons.append("alto histórico de notas operacionais")
    elif notas >= 3:
        reasons.append("histórico de notas operacionais")

    if recuperada > 0:
        reasons.append("histórico de energia recuperada")

    if not reasons:
        reasons.append("sem fator crítico dominante identificado")

    return reasons


def _to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0

    return float(value)


def _to_int(value: Any) -> int:
    if value in (None, ""):
        return 0

    return int(float(value))
