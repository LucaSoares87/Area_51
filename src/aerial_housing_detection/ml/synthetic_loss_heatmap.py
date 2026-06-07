import csv
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path("data/area51.db")
TRANSFORMER_HEATMAP_PATH = Path("reports/synthetic_loss_heatmap_transformers.csv")
FEEDER_HEATMAP_PATH = Path("reports/synthetic_loss_heatmap_feeders.csv")
SUMMARY_PATH = Path("reports/synthetic_loss_heatmap_summary.json")


@dataclass(frozen=True)
class SyntheticLossHeatmapResult:
    database_path: str
    transformer_heatmap_path: str
    feeder_heatmap_path: str
    summary_path: str
    transformer_rows: int
    feeder_rows: int
    high_heat_transformers: int
    high_heat_feeders: int


class SyntheticLossHeatmapBuilder:
    def __init__(
        self,
        db_path: Path = DB_PATH,
        transformer_heatmap_path: Path = TRANSFORMER_HEATMAP_PATH,
        feeder_heatmap_path: Path = FEEDER_HEATMAP_PATH,
        summary_path: Path = SUMMARY_PATH,
    ) -> None:
        self.db_path = db_path
        self.transformer_heatmap_path = transformer_heatmap_path
        self.feeder_heatmap_path = feeder_heatmap_path
        self.summary_path = summary_path

    def run(self) -> SyntheticLossHeatmapResult:
        transformer_rows = self._read_transformer_rows()
        feeder_rows = self._read_feeder_rows()

        transformer_heatmap = [
            build_transformer_heatmap_row(row) for row in transformer_rows
        ]
        feeder_heatmap = [build_feeder_heatmap_row(row) for row in feeder_rows]

        summary = build_heatmap_summary(transformer_heatmap, feeder_heatmap)

        self.transformer_heatmap_path.parent.mkdir(parents=True, exist_ok=True)
        self.feeder_heatmap_path.parent.mkdir(parents=True, exist_ok=True)
        self.summary_path.parent.mkdir(parents=True, exist_ok=True)

        self.transformer_heatmap_path.write_text(
            _to_csv(transformer_heatmap, TRANSFORMER_FIELDS),
            encoding="utf-8",
        )
        self.feeder_heatmap_path.write_text(
            _to_csv(feeder_heatmap, FEEDER_FIELDS),
            encoding="utf-8",
        )
        self.summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return SyntheticLossHeatmapResult(
            database_path=str(self.db_path),
            transformer_heatmap_path=str(self.transformer_heatmap_path),
            feeder_heatmap_path=str(self.feeder_heatmap_path),
            summary_path=str(self.summary_path),
            transformer_rows=len(transformer_heatmap),
            feeder_rows=len(feeder_heatmap),
            high_heat_transformers=int(summary["high_heat_transformers"]),
            high_heat_feeders=int(summary["high_heat_feeders"]),
        )

    def _read_transformer_rows(self) -> list[dict[str, Any]]:
        if not self.db_path.exists():
            return []

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row

            if not _table_exists(connection, "synthetic_transformer_heatmap"):
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
                    consumo_faturado_kwh,
                    energia_injetada_total,
                    perda_estimada_kwh,
                    perda_estimada_percentual,
                    qtd_irregularidades_confirmadas,
                    target_irregularidade_confirmada,
                    nivel_calor
                FROM synthetic_transformer_heatmap
                """
            ).fetchall()

            return [dict(row) for row in rows]

    def _read_feeder_rows(self) -> list[dict[str, Any]]:
        if not self.db_path.exists():
            return []

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row

            if not _table_exists(connection, "synthetic_feeder_heatmap"):
                return []

            rows = connection.execute(
                """
                SELECT
                    codigo_subestacao,
                    codigo_alimentador,
                    mes_referencia,
                    qtd_transformadores,
                    latitude_centroide,
                    longitude_centroide,
                    consumo_faturado_kwh,
                    perda_estimada_kwh,
                    perda_estimada_percentual_media,
                    qtd_irregularidades_confirmadas,
                    nivel_calor_alimentador
                FROM synthetic_feeder_heatmap
                """
            ).fetchall()

            return [dict(row) for row in rows]


def build_transformer_heatmap_row(row: dict[str, Any]) -> dict[str, Any]:
    perda_kwh = _to_float(row.get("perda_estimada_kwh"))
    perda_percentual = _to_float(row.get("perda_estimada_percentual"))
    irregularidades = _to_int(row.get("qtd_irregularidades_confirmadas"))
    consumo = _to_float(row.get("consumo_faturado_kwh"))

    heat_score = calculate_heat_score(
        perda_kwh=perda_kwh,
        perda_percentual=perda_percentual,
        irregularidades=irregularidades,
        consumo=consumo,
    )

    return {
        "codigo_transformador": row.get("codigo_transformador", ""),
        "codigo_subestacao": row.get("codigo_subestacao", ""),
        "codigo_alimentador": row.get("codigo_alimentador", ""),
        "mes_referencia": row.get("mes_referencia", ""),
        "latitude": _to_float(row.get("latitude")),
        "longitude": _to_float(row.get("longitude")),
        "consumo_faturado_kwh": consumo,
        "energia_injetada_total": _to_float(row.get("energia_injetada_total")),
        "perda_estimada_kwh": perda_kwh,
        "perda_estimada_percentual": perda_percentual,
        "qtd_irregularidades_confirmadas": irregularidades,
        "target_irregularidade_confirmada": _to_int(
            row.get("target_irregularidade_confirmada")
        ),
        "nivel_calor": classify_heat_level(heat_score),
        "heat_score": heat_score,
        "heat_reason": build_heat_reason(
            perda_kwh=perda_kwh,
            perda_percentual=perda_percentual,
            irregularidades=irregularidades,
        ),
    }


def build_feeder_heatmap_row(row: dict[str, Any]) -> dict[str, Any]:
    perda_kwh = _to_float(row.get("perda_estimada_kwh"))
    perda_percentual = _to_float(row.get("perda_estimada_percentual_media"))
    irregularidades = _to_int(row.get("qtd_irregularidades_confirmadas"))
    consumo = _to_float(row.get("consumo_faturado_kwh"))

    heat_score = calculate_heat_score(
        perda_kwh=perda_kwh,
        perda_percentual=perda_percentual,
        irregularidades=irregularidades,
        consumo=consumo,
    )

    return {
        "codigo_subestacao": row.get("codigo_subestacao", ""),
        "codigo_alimentador": row.get("codigo_alimentador", ""),
        "mes_referencia": row.get("mes_referencia", ""),
        "qtd_transformadores": _to_int(row.get("qtd_transformadores")),
        "latitude_centroide": _to_float(row.get("latitude_centroide")),
        "longitude_centroide": _to_float(row.get("longitude_centroide")),
        "consumo_faturado_kwh": consumo,
        "perda_estimada_kwh": perda_kwh,
        "perda_estimada_percentual_media": perda_percentual,
        "qtd_irregularidades_confirmadas": irregularidades,
        "nivel_calor_alimentador": classify_heat_level(heat_score),
        "heat_score": heat_score,
        "heat_reason": build_heat_reason(
            perda_kwh=perda_kwh,
            perda_percentual=perda_percentual,
            irregularidades=irregularidades,
        ),
    }


def calculate_heat_score(
    perda_kwh: float,
    perda_percentual: float,
    irregularidades: int,
    consumo: float,
) -> float:
    score = 0.0
    score += min(perda_kwh / 15000.0, 1.0) * 0.40
    score += min(perda_percentual / 0.35, 1.0) * 0.30
    score += min(irregularidades / 10.0, 1.0) * 0.20
    score += min(consumo / 80000.0, 1.0) * 0.10

    return round(max(0.0, min(score, 1.0)), 6)


def classify_heat_level(heat_score: float) -> str:
    if heat_score >= 0.70:
        return "ALTO"

    if heat_score >= 0.40:
        return "MEDIO"

    return "BAIXO"


def build_heat_reason(
    perda_kwh: float,
    perda_percentual: float,
    irregularidades: int,
) -> str:
    reasons: list[str] = []

    if perda_kwh >= 7000:
        reasons.append("perda_kwh_elevada")

    if perda_percentual >= 0.18:
        reasons.append("perda_percentual_elevada")

    if irregularidades > 0:
        reasons.append("irregularidades_confirmadas")

    if not reasons:
        reasons.append("baixo_indicador_de_perda")

    return "|".join(reasons)


def build_heatmap_summary(
    transformer_rows: list[dict[str, Any]],
    feeder_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "transformer_rows": len(transformer_rows),
        "feeder_rows": len(feeder_rows),
        "high_heat_transformers": sum(
            1 for row in transformer_rows if row["nivel_calor"] == "ALTO"
        ),
        "medium_heat_transformers": sum(
            1 for row in transformer_rows if row["nivel_calor"] == "MEDIO"
        ),
        "low_heat_transformers": sum(
            1 for row in transformer_rows if row["nivel_calor"] == "BAIXO"
        ),
        "high_heat_feeders": sum(
            1 for row in feeder_rows if row["nivel_calor_alimentador"] == "ALTO"
        ),
        "medium_heat_feeders": sum(
            1 for row in feeder_rows if row["nivel_calor_alimentador"] == "MEDIO"
        ),
        "low_heat_feeders": sum(
            1 for row in feeder_rows if row["nivel_calor_alimentador"] == "BAIXO"
        ),
        "average_transformer_heat_score": _average(
            [row["heat_score"] for row in transformer_rows]
        ),
        "average_feeder_heat_score": _average(
            [row["heat_score"] for row in feeder_rows]
        ),
    }


TRANSFORMER_FIELDS = [
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
    "target_irregularidade_confirmada",
    "nivel_calor",
    "heat_score",
    "heat_reason",
]

FEEDER_FIELDS = [
    "codigo_subestacao",
    "codigo_alimentador",
    "mes_referencia",
    "qtd_transformadores",
    "latitude_centroide",
    "longitude_centroide",
    "consumo_faturado_kwh",
    "perda_estimada_kwh",
    "perda_estimada_percentual_media",
    "qtd_irregularidades_confirmadas",
    "nivel_calor_alimentador",
    "heat_score",
    "heat_reason",
]


def _to_csv(rows: list[dict[str, Any]], fieldnames: list[str]) -> str:
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


def _average(values: list[float]) -> float:
    if not values:
        return 0.0

    return round(sum(values) / len(values), 6)


def _to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0

    return float(value)


def _to_int(value: Any) -> int:
    if value in (None, ""):
        return 0

    return int(float(value))
