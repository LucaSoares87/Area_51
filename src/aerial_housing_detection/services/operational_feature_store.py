import csv
import io
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path("data/area51.db")


@dataclass(frozen=True)
class OperationalFeatureStoreBuildResult:
    database_path: str
    table_name: str
    rows_created: int


class OperationalFeatureStore:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path

    def build(self) -> OperationalFeatureStoreBuildResult:
        if not self.db_path.exists():
            return OperationalFeatureStoreBuildResult(
                database_path=str(self.db_path),
                table_name="real_operational_features",
                rows_created=0,
            )

        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row

            self._create_table(connection)

            if not self._required_tables_exist(connection):
                connection.execute("DELETE FROM real_operational_features")
                return OperationalFeatureStoreBuildResult(
                    database_path=str(self.db_path),
                    table_name="real_operational_features",
                    rows_created=0,
                )

            rows = self._build_rows(connection)

            connection.execute("DELETE FROM real_operational_features")
            self._insert_rows(connection, rows)

        return OperationalFeatureStoreBuildResult(
            database_path=str(self.db_path),
            table_name="real_operational_features",
            rows_created=len(rows),
        )

    def get_transformer_features(self, transformer_code: str) -> dict[str, Any]:
        if not self.db_path.exists():
            return {
                "found": False,
                "message": "Banco local ainda não foi gerado.",
                "records": [],
            }

        try:
            with sqlite3.connect(self.db_path) as connection:
                connection.row_factory = sqlite3.Row

                if not self._table_exists(connection, "real_operational_features"):
                    return {
                        "found": False,
                        "message": "Feature store operacional ainda não foi criada.",
                        "records": [],
                    }

                rows = connection.execute(
                    """
                    SELECT *
                    FROM real_operational_features
                    WHERE codigo_transformador = ?
                    ORDER BY mes_referencia DESC
                    """,
                    (transformer_code.strip().upper(),),
                ).fetchall()

            return {
                "found": bool(rows),
                "codigo_transformador": transformer_code.strip().upper(),
                "records": [dict(row) for row in rows],
            }
        except sqlite3.OperationalError as error:
            return {
                "found": False,
                "message": "Feature store operacional indisponível.",
                "error": str(error),
                "records": [],
            }

    def get_ranking(self, limit: int = 50) -> dict[str, Any]:
        safe_limit = max(1, min(limit, 500))

        if not self.db_path.exists():
            return {
                "total_records": 0,
                "records": [],
                "message": "Banco local ainda não foi gerado.",
            }

        try:
            with sqlite3.connect(self.db_path) as connection:
                connection.row_factory = sqlite3.Row

                if not self._table_exists(connection, "real_operational_features"):
                    return {
                        "total_records": 0,
                        "records": [],
                        "message": "Feature store operacional ainda não foi criada.",
                    }

                rows = connection.execute(
                    """
                    SELECT *
                    FROM real_operational_features
                    ORDER BY risco_score DESC,
                             consumo_faturado_kwh DESC,
                             codigo_transformador ASC
                    LIMIT ?
                    """,
                    (safe_limit,),
                ).fetchall()

            return {
                "total_records": len(rows),
                "records": [dict(row) for row in rows],
            }
        except sqlite3.OperationalError as error:
            return {
                "total_records": 0,
                "records": [],
                "message": "Feature store operacional indisponível.",
                "error": str(error),
            }

    def export_csv(self) -> str:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=FEATURE_COLUMNS)
        writer.writeheader()

        if not self.db_path.exists():
            return output.getvalue()

        try:
            with sqlite3.connect(self.db_path) as connection:
                connection.row_factory = sqlite3.Row

                if not self._table_exists(connection, "real_operational_features"):
                    return output.getvalue()

                rows = connection.execute(
                    """
                    SELECT *
                    FROM real_operational_features
                    ORDER BY risco_score DESC,
                             consumo_faturado_kwh DESC,
                             codigo_transformador ASC,
                             mes_referencia DESC
                    """
                ).fetchall()

            for row in rows:
                writer.writerow(dict(row))
        except sqlite3.OperationalError:
            return output.getvalue()

        return output.getvalue()

    def _create_table(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS real_operational_features (
                codigo_transformador TEXT,
                codigo_subestacao TEXT,
                codigo_alimentador TEXT,
                mes_referencia TEXT,
                latitude REAL,
                longitude REAL,
                qtd_clientes INTEGER,
                qtd_clientes_com_consumo INTEGER,
                qtd_ligado INTEGER,
                qtd_cortado INTEGER,
                qtd_baixado INTEGER,
                consumo_faturado_kwh REAL,
                consumo_medio_por_cliente_ligado REAL,
                qtd_instalacoes_gd INTEGER,
                energia_injetada_total REAL,
                energia_injetada_fora_ponta REAL,
                energia_injetada_ponta REAL,
                qtd_notas INTEGER,
                energia_recuperada_media_kwh REAL,
                percentual_cortado REAL,
                percentual_baixado REAL,
                risco_score INTEGER,
                prioridade TEXT
            )
            """
        )

    def _required_tables_exist(self, connection: sqlite3.Connection) -> bool:
        required_tables = {
            "real_electrical_assets",
            "real_transformer_customers",
            "real_transformer_consumption_monthly",
            "real_transformer_gd_monthly",
            "real_customer_status_by_transformer",
            "real_transformer_notes",
            "real_recovered_energy",
        }

        existing_tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

        return required_tables.issubset(existing_tables)

    def _table_exists(self, connection: sqlite3.Connection, table_name: str) -> bool:
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

    def _build_rows(self, connection: sqlite3.Connection) -> list[dict[str, Any]]:
        consumption_rows = connection.execute(
            """
            SELECT *
            FROM real_transformer_consumption_monthly
            WHERE codigo_transformador IS NOT NULL
              AND codigo_transformador <> ''
              AND mes_referencia IS NOT NULL
              AND mes_referencia <> ''
            """
        ).fetchall()

        rows: list[dict[str, Any]] = []

        for consumption in consumption_rows:
            transformer_code = str(consumption["codigo_transformador"])
            month = str(consumption["mes_referencia"])

            asset = self._get_asset(connection, transformer_code)
            gd = self._get_gd(connection, transformer_code, month)
            status = self._get_customer_status(connection, transformer_code)
            notes = self._get_notes(connection, transformer_code)
            recovered_energy = self._get_recovered_energy(connection, transformer_code)
            customer_count = self._get_customer_count(connection, transformer_code)

            row = self._compose_feature_row(
                transformer_code=transformer_code,
                month=month,
                consumption=dict(consumption),
                asset=asset,
                gd=gd,
                status=status,
                notes=notes,
                recovered_energy=recovered_energy,
                customer_count=customer_count,
            )
            rows.append(row)

        return rows

    def _compose_feature_row(
        self,
        transformer_code: str,
        month: str,
        consumption: dict[str, Any],
        asset: dict[str, Any],
        gd: dict[str, Any],
        status: dict[str, Any],
        notes: dict[str, Any],
        recovered_energy: dict[str, Any],
        customer_count: int,
    ) -> dict[str, Any]:
        consumo_faturado = _to_float(consumption.get("consumo_faturado_kwh"))
        qtd_clientes_com_consumo = _to_int(
            consumption.get("qtd_clientes_com_consumo")
        )

        qtd_ligado = _to_int(status.get("qtd_ligado"))
        qtd_cortado = _to_int(status.get("qtd_cortado"))
        qtd_baixado = _to_int(status.get("qtd_baixado"))
        qtd_uc = _to_int(status.get("qtd_uc"))

        qtd_instalacoes_gd = _to_int(gd.get("qtd_instalacoes_gd"))
        energia_injetada_total = _to_float(gd.get("energia_injetada_total"))
        energia_injetada_fora_ponta = _to_float(
            gd.get("energia_injetada_fora_ponta")
        )
        energia_injetada_ponta = _to_float(gd.get("energia_injetada_ponta"))

        qtd_notas = _to_int(notes.get("qtd_notas"))
        energia_recuperada = _to_float(
            recovered_energy.get("energia_recuperada_media_kwh")
        )

        consumo_medio = _safe_divide(consumo_faturado, qtd_ligado)
        percentual_cortado = _safe_divide(qtd_cortado, qtd_uc)
        percentual_baixado = _safe_divide(qtd_baixado, qtd_uc)

        risco_score, prioridade = _calculate_risk_score(
            consumo_medio_por_cliente_ligado=consumo_medio,
            percentual_cortado=percentual_cortado,
            percentual_baixado=percentual_baixado,
            qtd_notas=qtd_notas,
            energia_recuperada_media_kwh=energia_recuperada,
            energia_injetada_total=energia_injetada_total,
        )

        return {
            "codigo_transformador": transformer_code,
            "codigo_subestacao": (
                asset.get("codigo_subestacao")
                or consumption.get("codigo_subestacao")
            ),
            "codigo_alimentador": (
                asset.get("codigo_alimentador")
                or consumption.get("codigo_alimentador")
            ),
            "mes_referencia": month,
            "latitude": asset.get("latitude"),
            "longitude": asset.get("longitude"),
            "qtd_clientes": customer_count,
            "qtd_clientes_com_consumo": qtd_clientes_com_consumo,
            "qtd_ligado": qtd_ligado,
            "qtd_cortado": qtd_cortado,
            "qtd_baixado": qtd_baixado,
            "consumo_faturado_kwh": consumo_faturado,
            "consumo_medio_por_cliente_ligado": round(consumo_medio, 2),
            "qtd_instalacoes_gd": qtd_instalacoes_gd,
            "energia_injetada_total": energia_injetada_total,
            "energia_injetada_fora_ponta": energia_injetada_fora_ponta,
            "energia_injetada_ponta": energia_injetada_ponta,
            "qtd_notas": qtd_notas,
            "energia_recuperada_media_kwh": energia_recuperada,
            "percentual_cortado": round(percentual_cortado, 4),
            "percentual_baixado": round(percentual_baixado, 4),
            "risco_score": risco_score,
            "prioridade": prioridade,
        }

    def _insert_rows(
        self,
        connection: sqlite3.Connection,
        rows: list[dict[str, Any]],
    ) -> None:
        if not rows:
            return

        placeholders = ", ".join(["?"] * len(FEATURE_COLUMNS))
        columns_sql = ", ".join(FEATURE_COLUMNS)

        sql = (
            f"INSERT INTO real_operational_features ({columns_sql}) "
            f"VALUES ({placeholders})"
        )

        for row in rows:
            connection.execute(
                sql,
                tuple(row.get(column) for column in FEATURE_COLUMNS),
            )

    def _get_asset(
        self,
        connection: sqlite3.Connection,
        transformer_code: str,
    ) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT *
            FROM real_electrical_assets
            WHERE codigo_transformador = ?
            LIMIT 1
            """,
            (transformer_code,),
        ).fetchone()

        return dict(row) if row else {}

    def _get_gd(
        self,
        connection: sqlite3.Connection,
        transformer_code: str,
        month: str,
    ) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT *
            FROM real_transformer_gd_monthly
            WHERE codigo_transformador = ?
              AND mes_referencia = ?
            LIMIT 1
            """,
            (transformer_code, month),
        ).fetchone()

        return dict(row) if row else {}

    def _get_customer_status(
        self,
        connection: sqlite3.Connection,
        transformer_code: str,
    ) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT *
            FROM real_customer_status_by_transformer
            WHERE codigo_transformador = ?
            LIMIT 1
            """,
            (transformer_code,),
        ).fetchone()

        return dict(row) if row else {}

    def _get_notes(
        self,
        connection: sqlite3.Connection,
        transformer_code: str,
    ) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT
                codigo_transformador,
                SUM(COALESCE(quantidade_notas, 0)) AS qtd_notas
            FROM real_transformer_notes
            WHERE codigo_transformador = ?
            GROUP BY codigo_transformador
            """,
            (transformer_code,),
        ).fetchone()

        return dict(row) if row else {"qtd_notas": 0}

    def _get_recovered_energy(
        self,
        connection: sqlite3.Connection,
        transformer_code: str,
    ) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT *
            FROM real_recovered_energy
            WHERE codigo_transformador = ?
            LIMIT 1
            """,
            (transformer_code,),
        ).fetchone()

        return dict(row) if row else {}

    def _get_customer_count(
        self,
        connection: sqlite3.Connection,
        transformer_code: str,
    ) -> int:
        row = connection.execute(
            """
            SELECT COUNT(DISTINCT instalacao) AS qtd_clientes
            FROM real_transformer_customers
            WHERE codigo_transformador = ?
            """,
            (transformer_code,),
        ).fetchone()

        if row is None:
            return 0

        return _to_int(row["qtd_clientes"])


FEATURE_COLUMNS = [
    "codigo_transformador",
    "codigo_subestacao",
    "codigo_alimentador",
    "mes_referencia",
    "latitude",
    "longitude",
    "qtd_clientes",
    "qtd_clientes_com_consumo",
    "qtd_ligado",
    "qtd_cortado",
    "qtd_baixado",
    "consumo_faturado_kwh",
    "consumo_medio_por_cliente_ligado",
    "qtd_instalacoes_gd",
    "energia_injetada_total",
    "energia_injetada_fora_ponta",
    "energia_injetada_ponta",
    "qtd_notas",
    "energia_recuperada_media_kwh",
    "percentual_cortado",
    "percentual_baixado",
    "risco_score",
    "prioridade",
]


def _calculate_risk_score(
    consumo_medio_por_cliente_ligado: float,
    percentual_cortado: float,
    percentual_baixado: float,
    qtd_notas: int,
    energia_recuperada_media_kwh: float,
    energia_injetada_total: float,
) -> tuple[int, str]:
    score = 0

    if consumo_medio_por_cliente_ligado >= 350:
        score += 20
    elif consumo_medio_por_cliente_ligado >= 220:
        score += 10

    if percentual_cortado >= 0.20:
        score += 20
    elif percentual_cortado >= 0.10:
        score += 10

    if percentual_baixado >= 0.10:
        score += 10

    if qtd_notas >= 10:
        score += 20
    elif qtd_notas >= 3:
        score += 10

    if energia_recuperada_media_kwh > 0:
        score += 15

    if energia_injetada_total > 0:
        score += 5

    score = min(score, 100)

    if score >= 70:
        return score, "Alta"

    if score >= 40:
        return score, "Média"

    return score, "Baixa"


def _safe_divide(numerator: float | int, denominator: float | int) -> float:
    if denominator in (0, None):
        return 0.0

    return float(numerator or 0) / float(denominator)


def _to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0

    return float(value)


def _to_int(value: Any) -> int:
    if value in (None, ""):
        return 0

    return int(value)