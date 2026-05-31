import csv
import io
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path("data/area51.db")
OUTPUT_PATH = Path("data/processed/ml_transformer_dataset.csv")


@dataclass(frozen=True)
class MlDatasetBuildResult:
    database_path: str
    output_path: str
    rows_created: int
    columns: list[str]


class TransformerMlDatasetBuilder:
    def __init__(
        self,
        db_path: Path = DB_PATH,
        output_path: Path = OUTPUT_PATH,
    ) -> None:
        self.db_path = db_path
        self.output_path = output_path

    def build(self) -> MlDatasetBuildResult:
        rows = self.build_rows()

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        content = self.to_csv(rows)
        self.output_path.write_text(content, encoding="utf-8")

        return MlDatasetBuildResult(
            database_path=str(self.db_path),
            output_path=str(self.output_path),
            rows_created=len(rows),
            columns=ML_DATASET_COLUMNS,
        )

    def build_rows(self) -> list[dict[str, Any]]:
        if not self.db_path.exists():
            return []

        try:
            with sqlite3.connect(self.db_path) as connection:
                connection.row_factory = sqlite3.Row

                if not self._table_exists(connection, "real_operational_features"):
                    return []

                source_rows = connection.execute(
                    """
                    SELECT *
                    FROM real_operational_features
                    ORDER BY codigo_transformador ASC,
                             mes_referencia ASC
                    """
                ).fetchall()

                return [self._build_ml_row(dict(row)) for row in source_rows]
        except sqlite3.OperationalError:
            return []

    def to_csv(self, rows: list[dict[str, Any]]) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=ML_DATASET_COLUMNS)
        writer.writeheader()

        for row in rows:
            writer.writerow({column: row.get(column) for column in ML_DATASET_COLUMNS})

        return output.getvalue()

    def _build_ml_row(self, row: dict[str, Any]) -> dict[str, Any]:
        risco_score = _to_int(row.get("risco_score"))
        consumo = _to_float(row.get("consumo_faturado_kwh"))
        qtd_ligado = _to_int(row.get("qtd_ligado"))
        qtd_cortado = _to_int(row.get("qtd_cortado"))
        qtd_baixado = _to_int(row.get("qtd_baixado"))
        qtd_clientes = _to_int(row.get("qtd_clientes"))
        qtd_notas = _to_int(row.get("qtd_notas"))
        gd_total = _to_float(row.get("energia_injetada_total"))
        recuperada = _to_float(row.get("energia_recuperada_media_kwh"))

        percentual_cortado = _to_float(row.get("percentual_cortado"))
        percentual_baixado = _to_float(row.get("percentual_baixado"))

        return {
            "codigo_transformador": row.get("codigo_transformador"),
            "codigo_subestacao": row.get("codigo_subestacao"),
            "codigo_alimentador": row.get("codigo_alimentador"),
            "mes_referencia": row.get("mes_referencia"),
            "latitude": row.get("latitude"),
            "longitude": row.get("longitude"),
            "qtd_clientes": qtd_clientes,
            "qtd_ligado": qtd_ligado,
            "qtd_cortado": qtd_cortado,
            "qtd_baixado": qtd_baixado,
            "consumo_faturado_kwh": consumo,
            "consumo_medio_por_cliente_ligado": _to_float(
                row.get("consumo_medio_por_cliente_ligado")
            ),
            "qtd_instalacoes_gd": _to_int(row.get("qtd_instalacoes_gd")),
            "energia_injetada_total": gd_total,
            "qtd_notas": qtd_notas,
            "energia_recuperada_media_kwh": recuperada,
            "percentual_cortado": percentual_cortado,
            "percentual_baixado": percentual_baixado,
            "tem_gd": 1 if gd_total > 0 else 0,
            "tem_energia_recuperada": 1 if recuperada > 0 else 0,
            "tem_notas": 1 if qtd_notas > 0 else 0,
            "clientes_nao_ligados": qtd_cortado + qtd_baixado,
            "percentual_nao_ligado": _safe_divide(
                qtd_cortado + qtd_baixado,
                max(qtd_clientes, qtd_ligado + qtd_cortado + qtd_baixado),
            ),
            "risco_score": risco_score,
            "prioridade": row.get("prioridade"),
            "target_risco_alto": 1 if risco_score >= 70 else 0,
        }

    def _table_exists(
        self,
        connection: sqlite3.Connection,
        table_name: str,
    ) -> bool:
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


ML_DATASET_COLUMNS = [
    "codigo_transformador",
    "codigo_subestacao",
    "codigo_alimentador",
    "mes_referencia",
    "latitude",
    "longitude",
    "qtd_clientes",
    "qtd_ligado",
    "qtd_cortado",
    "qtd_baixado",
    "consumo_faturado_kwh",
    "consumo_medio_por_cliente_ligado",
    "qtd_instalacoes_gd",
    "energia_injetada_total",
    "qtd_notas",
    "energia_recuperada_media_kwh",
    "percentual_cortado",
    "percentual_baixado",
    "tem_gd",
    "tem_energia_recuperada",
    "tem_notas",
    "clientes_nao_ligados",
    "percentual_nao_ligado",
    "risco_score",
    "prioridade",
    "target_risco_alto",
]


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

    return int(value)