import csv
import io
import json
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path("data/area51.db")
CRAS_PATH = Path("data/demo/cras_simulado.json")
IBGE_PATH = Path("data/demo/ibge_simulado.json")


@dataclass(frozen=True)
class RealisticAnalysisRequest:
    latitude: float
    longitude: float
    radius_meters: int = 600


class RealisticDemoAnalysisService:
    def __init__(
        self,
        db_path: Path = DB_PATH,
        cras_path: Path = CRAS_PATH,
        ibge_path: Path = IBGE_PATH,
    ) -> None:
        self.db_path = db_path
        self.cras_path = cras_path
        self.ibge_path = ibge_path

    def analyze(self, request: RealisticAnalysisRequest) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as connection:
            connection.row_factory = sqlite3.Row
            transformers = self._get_transformers(connection)

            if not transformers:
                return self._empty_result(request)

            enriched = [
                self._build_transformer_analysis(connection, transformer, request)
                for transformer in transformers
            ]
            selected = min(enriched, key=lambda item: item["distance_meters"])

        return {
            "query": {
                "latitude": request.latitude,
                "longitude": request.longitude,
                "radius_meters": request.radius_meters,
            },
            "selected_transformer": selected,
            "transformers": enriched,
            "summary": self._build_summary(selected),
        }

    def export_csv(self, request: RealisticAnalysisRequest) -> str:
        analysis = self.analyze(request)
        rows = analysis["transformers"]

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "transformer_code",
                "feeder_code",
                "substation_code",
                "power_kva",
                "latitude",
                "longitude",
                "distance_meters",
                "measured_energy_kwh",
                "received_gd_energy_kwh",
                "injected_energy_kwh",
                "total_area_energy_kwh",
                "customer_count",
                "customer_consumption_kwh",
                "cras_houses",
                "ibge_houses",
                "roof_houses",
                "estimated_houses_average",
                "estimated_houses_min",
                "estimated_houses_max",
                "cras_people",
                "ibge_people",
                "estimated_loss_kwh",
                "estimated_loss_percent",
                "estimated_consumption_per_house_kwh",
                "priority",
            ],
        )
        writer.writeheader()

        for row in rows:
            houses = row["houses"]
            people = row["people"]
            energy = row["energy"]
            writer.writerow(
                {
                    "transformer_code": row["transformer_code"],
                    "feeder_code": row["feeder_code"],
                    "substation_code": row["substation_code"],
                    "power_kva": row["power_kva"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "distance_meters": row["distance_meters"],
                    "measured_energy_kwh": energy["measured_energy_kwh"],
                    "received_gd_energy_kwh": energy["received_gd_energy_kwh"],
                    "injected_energy_kwh": energy["injected_energy_kwh"],
                    "total_area_energy_kwh": energy["total_area_energy_kwh"],
                    "customer_count": row["customer_count"],
                    "customer_consumption_kwh": energy["customer_consumption_kwh"],
                    "cras_houses": houses["cras"],
                    "ibge_houses": houses["ibge"],
                    "roof_houses": houses["roof_image"],
                    "estimated_houses_average": houses["average"],
                    "estimated_houses_min": houses["estimated_range"]["min"],
                    "estimated_houses_max": houses["estimated_range"]["max"],
                    "cras_people": people["cras"],
                    "ibge_people": people["ibge"],
                    "estimated_loss_kwh": energy["estimated_loss_kwh"],
                    "estimated_loss_percent": energy["estimated_loss_percent"],
                    "estimated_consumption_per_house_kwh": (
                        energy["estimated_consumption_per_house_kwh"]
                    ),
                    "priority": row["priority"],
                }
            )

        return output.getvalue()

    def _get_transformers(self, connection: sqlite3.Connection) -> list[sqlite3.Row]:
        return list(
            connection.execute(
                """
                SELECT
                    transformer_code,
                    power_kva,
                    feeder_code,
                    substation_code,
                    latitude,
                    longitude,
                    measured_energy_kwh,
                    injected_energy_kwh,
                    received_gd_energy_kwh,
                    technical_loss_kwh
                FROM demo_transformers
                """
            )
        )

    def _build_transformer_analysis(
        self,
        connection: sqlite3.Connection,
        transformer: sqlite3.Row,
        request: RealisticAnalysisRequest,
    ) -> dict[str, Any]:
        transformer_code = str(transformer["transformer_code"])
        aggregate = self._get_customer_aggregate(connection, transformer_code)
        roof = self._get_roof_estimate(connection, transformer_code)
        cras = self._load_cras_context()
        ibge = self._load_ibge_context()

        distance_meters = _distance_meters(
            request.latitude,
            request.longitude,
            float(transformer["latitude"]),
            float(transformer["longitude"]),
        )

        customer_count = int(aggregate["customer_count"]) if aggregate else 0
        customer_consumption = (
            float(aggregate["total_consumption_kwh"]) if aggregate else 0.0
        )
        measured_energy = float(transformer["measured_energy_kwh"])
        received_gd = float(transformer["received_gd_energy_kwh"])
        injected_energy = float(transformer["injected_energy_kwh"])
        technical_loss = float(transformer["technical_loss_kwh"])

        houses = self._build_house_estimation(cras, ibge, roof)
        people = {
            "cras": int(cras["estimated_people"]),
            "ibge": int(ibge["estimated_people"]),
        }
        energy = self._build_energy_result(
            measured_energy=measured_energy,
            customer_consumption=customer_consumption,
            received_gd=received_gd,
            injected_energy=injected_energy,
            technical_loss=technical_loss,
            estimated_houses=houses["average"],
        )
        priority = self._priority(energy["estimated_loss_percent"], distance_meters)

        return {
            "transformer_code": transformer_code,
            "feeder_code": transformer["feeder_code"],
            "substation_code": transformer["substation_code"],
            "power_kva": transformer["power_kva"],
            "latitude": transformer["latitude"],
            "longitude": transformer["longitude"],
            "distance_meters": round(distance_meters, 2),
            "customer_count": customer_count,
            "houses": houses,
            "people": people,
            "energy": energy,
            "territory": {
                "cras": cras,
                "ibge": ibge,
            },
            "priority": priority,
        }

    def _get_customer_aggregate(
        self,
        connection: sqlite3.Connection,
        transformer_code: str,
    ) -> sqlite3.Row | None:
        return connection.execute(
            """
            SELECT
                transformer_code,
                customer_count,
                total_consumption_kwh
            FROM demo_customer_aggregates
            WHERE transformer_code = ?
            """,
            (transformer_code,),
        ).fetchone()

    def _get_roof_estimate(
        self,
        connection: sqlite3.Connection,
        transformer_code: str,
    ) -> sqlite3.Row | None:
        return connection.execute(
            """
            SELECT
                transformer_code,
                estimated_roofs,
                confidence_score,
                source
            FROM demo_roof_estimates
            WHERE transformer_code = ?
            """,
            (transformer_code,),
        ).fetchone()

    def _load_cras_context(self) -> dict[str, Any]:
        payload = json.loads(self.cras_path.read_text(encoding="utf-8"))
        return payload["territories"][0]

    def _load_ibge_context(self) -> dict[str, Any]:
        payload = json.loads(self.ibge_path.read_text(encoding="utf-8"))
        return payload["sectors"][0]

    def _build_house_estimation(
        self,
        cras: dict[str, Any],
        ibge: dict[str, Any],
        roof: sqlite3.Row | None,
    ) -> dict[str, Any]:
        cras_houses = int(cras["estimated_houses"])
        ibge_houses = int(ibge["estimated_houses"])
        roof_houses = int(roof["estimated_roofs"]) if roof else None

        values = [cras_houses, ibge_houses]
        if roof_houses is not None:
            values.append(roof_houses)

        average = round(sum(values) / len(values))
        return {
            "cras": cras_houses,
            "ibge": ibge_houses,
            "roof_image": roof_houses,
            "average": average,
            "estimated_range": {
                "min": max(average - 2, 0),
                "max": average + 2,
            },
        }

    def _build_energy_result(
        self,
        measured_energy: float,
        customer_consumption: float,
        received_gd: float,
        injected_energy: float,
        technical_loss: float,
        estimated_houses: int,
    ) -> dict[str, Any]:
        total_area_energy = measured_energy + received_gd
        estimated_loss = (
            total_area_energy
            - customer_consumption
            - injected_energy
            - technical_loss
        )
        estimated_loss = max(estimated_loss, 0.0)

        estimated_loss_percent = 0.0
        if total_area_energy > 0:
            estimated_loss_percent = (estimated_loss / total_area_energy) * 100

        consumption_per_house = 0.0
        if estimated_houses > 0:
            consumption_per_house = customer_consumption / estimated_houses

        return {
            "measured_energy_kwh": round(measured_energy, 2),
            "received_gd_energy_kwh": round(received_gd, 2),
            "injected_energy_kwh": round(injected_energy, 2),
            "total_area_energy_kwh": round(total_area_energy, 2),
            "customer_consumption_kwh": round(customer_consumption, 2),
            "technical_loss_kwh": round(technical_loss, 2),
            "estimated_loss_kwh": round(estimated_loss, 2),
            "estimated_loss_percent": round(estimated_loss_percent, 2),
            "estimated_consumption_per_house_kwh": round(consumption_per_house, 2),
        }

    def _priority(self, estimated_loss_percent: float, distance_meters: float) -> str:
        if estimated_loss_percent >= 18 and distance_meters <= 600:
            return "Alta"

        if estimated_loss_percent >= 10:
            return "Média"

        return "Baixa"

    def _build_summary(self, selected: dict[str, Any]) -> dict[str, Any]:
        houses = selected["houses"]
        energy = selected["energy"]

        return {
            "message": (
                "Área analisada com base em transformador, clientes, GD, "
                "CRAS, IBGE e telhados estimados."
            ),
            "selected_transformer": selected["transformer_code"],
            "feeder_code": selected["feeder_code"],
            "substation_code": selected["substation_code"],
            "estimated_houses_text": (
                f"Estimamos que tenha entre {houses['estimated_range']['min']} "
                f"e {houses['estimated_range']['max']} casas."
            ),
            "estimated_loss_kwh": energy["estimated_loss_kwh"],
            "estimated_loss_percent": energy["estimated_loss_percent"],
            "priority": selected["priority"],
        }

    def _empty_result(self, request: RealisticAnalysisRequest) -> dict[str, Any]:
        return {
            "query": {
                "latitude": request.latitude,
                "longitude": request.longitude,
                "radius_meters": request.radius_meters,
            },
            "selected_transformer": None,
            "transformers": [],
            "summary": {
                "message": "Nenhum transformador encontrado na base demo.",
                "priority": "Indefinida",
            },
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