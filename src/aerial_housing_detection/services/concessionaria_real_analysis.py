import csv
import io
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path("data/area51.db")


@dataclass(frozen=True)
class RealConcessionariaAnalysisRequest:
    transformer_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class ConcessionariaRealAnalysisService:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path

    def analyze(
        self,
        request: RealConcessionariaAnalysisRequest,
    ) -> dict[str, Any]:
        if not self.db_path.exists():
            return {
                "found": False,
                "message": "Banco local da concessionária ainda não foi importado.",
                "query": request.__dict__,
            }

        try:
            with sqlite3.connect(self.db_path) as connection:
                connection.row_factory = sqlite3.Row

                asset = self._select_asset(connection, request)

                if asset is None:
                    return {
                        "found": False,
                        "message": "Nenhum transformador encontrado.",
                        "query": request.__dict__,
                    }

                transformer_code = str(asset["codigo_transformador"])
                consumption = self._latest_consumption(connection, transformer_code)
                gd = self._latest_gd(connection, transformer_code)
                status = self._customer_status(connection, transformer_code)
                notes = self._notes_summary(connection, transformer_code)
                recovered_energy = self._recovered_energy(connection, transformer_code)

                indicators = self._build_indicators(
                    consumption=consumption,
                    gd=gd,
                    status=status,
                    notes=notes,
                    recovered_energy=recovered_energy,
                )

                return {
                    "found": True,
                    "asset": dict(asset),
                    "consumption": consumption,
                    "gd": gd,
                    "customer_status": status,
                    "notes": notes,
                    "recovered_energy": recovered_energy,
                    "indicators": indicators,
                }
        except sqlite3.OperationalError as error:
            return {
                "found": False,
                "message": (
                    "Banco local da concessionária não está pronto. "
                    "Execute python -m scripts.import_concessionaria_csvs."
                ),
                "error": str(error),
                "query": request.__dict__,
            }

            transformer_code = str(asset["codigo_transformador"])
            consumption = self._latest_consumption(connection, transformer_code)
            gd = self._latest_gd(connection, transformer_code)
            status = self._customer_status(connection, transformer_code)
            notes = self._notes_summary(connection, transformer_code)
            recovered_energy = self._recovered_energy(connection, transformer_code)

            indicators = self._build_indicators(
                consumption=consumption,
                gd=gd,
                status=status,
                notes=notes,
                recovered_energy=recovered_energy,
            )

            return {
                "found": True,
                "asset": dict(asset),
                "consumption": consumption,
                "gd": gd,
                "customer_status": status,
                "notes": notes,
                "recovered_energy": recovered_energy,
                "indicators": indicators,
            }

    def export_csv(
        self,
        request: RealConcessionariaAnalysisRequest,
    ) -> str:
        result = self.analyze(request)

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "codigo_transformador",
                "codigo_subestacao",
                "codigo_alimentador",
                "latitude",
                "longitude",
                "mes_referencia",
                "qtd_clientes_com_consumo",
                "consumo_faturado_kwh",
                "qtd_instalacoes_gd",
                "energia_injetada_total",
                "qtd_uc",
                "qtd_ligado",
                "qtd_cortado",
                "qtd_baixado",
                "qtd_notas",
                "energia_recuperada_media_kwh",
                "consumo_medio_por_cliente_ligado",
                "risco_score",
                "prioridade",
            ],
        )
        writer.writeheader()

        if not result.get("found"):
            return output.getvalue()

        asset = result["asset"]
        consumption = result["consumption"]
        gd = result["gd"]
        status = result["customer_status"]
        notes = result["notes"]
        recovered_energy = result["recovered_energy"]
        indicators = result["indicators"]

        writer.writerow(
            {
                "codigo_transformador": asset.get("codigo_transformador"),
                "codigo_subestacao": asset.get("codigo_subestacao"),
                "codigo_alimentador": asset.get("codigo_alimentador"),
                "latitude": asset.get("latitude"),
                "longitude": asset.get("longitude"),
                "mes_referencia": consumption.get("mes_referencia"),
                "qtd_clientes_com_consumo": consumption.get(
                    "qtd_clientes_com_consumo"
                ),
                "consumo_faturado_kwh": consumption.get("consumo_faturado_kwh"),
                "qtd_instalacoes_gd": gd.get("qtd_instalacoes_gd"),
                "energia_injetada_total": gd.get("energia_injetada_total"),
                "qtd_uc": status.get("qtd_uc"),
                "qtd_ligado": status.get("qtd_ligado"),
                "qtd_cortado": status.get("qtd_cortado"),
                "qtd_baixado": status.get("qtd_baixado"),
                "qtd_notas": notes.get("qtd_notas"),
                "energia_recuperada_media_kwh": recovered_energy.get(
                    "energia_recuperada_media_kwh"
                ),
                "consumo_medio_por_cliente_ligado": indicators.get(
                    "consumo_medio_por_cliente_ligado"
                ),
                "risco_score": indicators.get("risco_score"),
                "prioridade": indicators.get("prioridade"),
            }
        )

        return output.getvalue()

    def _select_asset(
        self,
        connection: sqlite3.Connection,
        request: RealConcessionariaAnalysisRequest,
    ) -> sqlite3.Row | None:
        if request.transformer_code:
            return connection.execute(
                """
                SELECT *
                FROM real_electrical_assets
                WHERE codigo_transformador = ?
                LIMIT 1
                """,
                (request.transformer_code.strip().upper(),),
            ).fetchone()

        if request.latitude is not None and request.longitude is not None:
            assets = list(
                connection.execute(
                    """
                    SELECT *
                    FROM real_electrical_assets
                    WHERE latitude IS NOT NULL
                      AND longitude IS NOT NULL
                    """
                )
            )

            if not assets:
                return None

            return min(
                assets,
                key=lambda item: _distance_meters(
                    float(request.latitude),
                    float(request.longitude),
                    float(item["latitude"]),
                    float(item["longitude"]),
                ),
            )

        return None

    def _latest_consumption(
        self,
        connection: sqlite3.Connection,
        transformer_code: str,
    ) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT *
            FROM real_transformer_consumption_monthly
            WHERE codigo_transformador = ?
            ORDER BY mes_referencia DESC
            LIMIT 1
            """,
            (transformer_code,),
        ).fetchone()

        return dict(row) if row else {}

    def _latest_gd(
        self,
        connection: sqlite3.Connection,
        transformer_code: str,
    ) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT *
            FROM real_transformer_gd_monthly
            WHERE codigo_transformador = ?
            ORDER BY mes_referencia DESC
            LIMIT 1
            """,
            (transformer_code,),
        ).fetchone()

        return dict(row) if row else {}

    def _customer_status(
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

    def _notes_summary(
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

    def _recovered_energy(
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

    def _build_indicators(
        self,
        consumption: dict[str, Any],
        gd: dict[str, Any],
        status: dict[str, Any],
        notes: dict[str, Any],
        recovered_energy: dict[str, Any],
    ) -> dict[str, Any]:
        consumo = float(consumption.get("consumo_faturado_kwh") or 0)
        ligados = int(status.get("qtd_ligado") or 0)
        cortados = int(status.get("qtd_cortado") or 0)
        baixados = int(status.get("qtd_baixado") or 0)
        notas = int(notes.get("qtd_notas") or 0)
        gd_injetada = float(gd.get("energia_injetada_total") or 0)
        energia_recuperada = float(
            recovered_energy.get("energia_recuperada_media_kwh") or 0
        )

        consumo_medio = 0.0
        if ligados > 0:
            consumo_medio = consumo / ligados

        score = 0

        if consumo_medio >= 350:
            score += 20
        elif consumo_medio >= 220:
            score += 10

        if cortados >= 20:
            score += 20
        elif cortados >= 5:
            score += 10

        if baixados >= 10:
            score += 10

        if notas >= 10:
            score += 20
        elif notas >= 3:
            score += 10

        if energia_recuperada > 0:
            score += 15

        if gd_injetada > 0:
            score += 5

        score = min(score, 100)

        if score >= 70:
            prioridade = "Alta"
        elif score >= 40:
            prioridade = "Média"
        else:
            prioridade = "Baixa"

        return {
            "consumo_medio_por_cliente_ligado": round(consumo_medio, 2),
            "risco_score": score,
            "prioridade": prioridade,
            "metodo": (
                "Score de risco baseado em consumo faturado, clientes ligados, "
                "cortados, baixados, notas, GD e energia recuperada histórica."
            ),
        }


def _distance_meters(
    origin_latitude: float,
    origin_longitude: float,
    target_latitude: float,
    target_longitude: float,
) -> float:
    radius_meters = 6371000.0
    delta_latitude = math.radians(target_latitude - origin_latitude)
    delta_longitude = math.radians(target_longitude - origin_longitude)

    lat1 = math.radians(origin_latitude)
    lat2 = math.radians(target_latitude)

    value = (
        math.sin(delta_latitude / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_longitude / 2) ** 2
    )

    return radius_meters * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))
