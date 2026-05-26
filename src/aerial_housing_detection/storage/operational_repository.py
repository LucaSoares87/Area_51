import math
import sqlite3
from pathlib import Path

from src.aerial_housing_detection.domain.operational_search import (
    CustomerOperationalLink,
    OperationalAsset,
)


class OperationalRepository:
    def __init__(self, database_path: Path | str = "data/area51.db") -> None:
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS operational_assets (
                    area_id TEXT PRIMARY KEY,
                    transformer_code TEXT NOT NULL,
                    feeder_code TEXT NOT NULL,
                    substation_code TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    city TEXT NOT NULL,
                    neighborhood TEXT NOT NULL,
                    installed_power_kva REAL,
                    operational_status TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS customer_operational_links (
                    customer_id TEXT NOT NULL,
                    area_id TEXT NOT NULL,
                    transformer_code TEXT NOT NULL,
                    feeder_code TEXT NOT NULL,
                    substation_code TEXT NOT NULL,
                    reference_month TEXT NOT NULL,
                    customer_status TEXT,
                    consumer_class TEXT,
                    PRIMARY KEY (customer_id, reference_month)
                )
                """
            )

    def save_asset(self, asset: OperationalAsset) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO operational_assets (
                    area_id,
                    transformer_code,
                    feeder_code,
                    substation_code,
                    latitude,
                    longitude,
                    city,
                    neighborhood,
                    installed_power_kva,
                    operational_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(area_id) DO UPDATE SET
                    transformer_code = excluded.transformer_code,
                    feeder_code = excluded.feeder_code,
                    substation_code = excluded.substation_code,
                    latitude = excluded.latitude,
                    longitude = excluded.longitude,
                    city = excluded.city,
                    neighborhood = excluded.neighborhood,
                    installed_power_kva = excluded.installed_power_kva,
                    operational_status = excluded.operational_status
                """,
                (
                    asset.area_id,
                    asset.transformer_code,
                    asset.feeder_code,
                    asset.substation_code,
                    asset.latitude,
                    asset.longitude,
                    asset.city,
                    asset.neighborhood,
                    asset.installed_power_kva,
                    asset.operational_status,
                ),
            )

    def save_customer_link(self, link: CustomerOperationalLink) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO customer_operational_links (
                    customer_id,
                    area_id,
                    transformer_code,
                    feeder_code,
                    substation_code,
                    reference_month,
                    customer_status,
                    consumer_class
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(customer_id, reference_month) DO UPDATE SET
                    area_id = excluded.area_id,
                    transformer_code = excluded.transformer_code,
                    feeder_code = excluded.feeder_code,
                    substation_code = excluded.substation_code,
                    customer_status = excluded.customer_status,
                    consumer_class = excluded.consumer_class
                """,
                (
                    link.customer_id,
                    link.area_id,
                    link.transformer_code,
                    link.feeder_code,
                    link.substation_code,
                    link.reference_month,
                    link.customer_status,
                    link.consumer_class,
                ),
            )

    def get_asset_by_area(self, area_id: str) -> OperationalAsset | None:
        return self._get_single_asset(
            "SELECT * FROM operational_assets WHERE area_id = ?",
            (area_id,),
        )

    def get_asset_by_transformer(self, transformer_code: str) -> OperationalAsset | None:
        return self._get_single_asset(
            "SELECT * FROM operational_assets WHERE transformer_code = ?",
            (transformer_code,),
        )

    def get_assets_by_feeder(self, feeder_code: str) -> list[OperationalAsset]:
        return self._get_assets(
            "SELECT * FROM operational_assets WHERE feeder_code = ?",
            (feeder_code,),
        )

    def get_assets_by_substation(self, substation_code: str) -> list[OperationalAsset]:
        return self._get_assets(
            "SELECT * FROM operational_assets WHERE substation_code = ?",
            (substation_code,),
        )

    def get_customer_link(
        self,
        customer_id: str,
        reference_month: str,
    ) -> CustomerOperationalLink | None:
        query = """
            SELECT *
            FROM customer_operational_links
            WHERE customer_id = ?
              AND reference_month = ?
        """

        with self._connect() as connection:
            row = connection.execute(query, (customer_id, reference_month)).fetchone()

        if row is None:
            return None

        return self._row_to_customer_link(row)

    def find_nearest_asset(
        self,
        latitude: float,
        longitude: float,
    ) -> tuple[OperationalAsset, float] | None:
        assets = self._get_assets("SELECT * FROM operational_assets", ())

        if not assets:
            return None

        ranked = [
            (
                asset,
                self._haversine_distance_meters(
                    latitude,
                    longitude,
                    asset.latitude,
                    asset.longitude,
                ),
            )
            for asset in assets
        ]

        return min(ranked, key=lambda item: item[1])

    def _get_single_asset(
        self,
        query: str,
        parameters: tuple[object, ...],
    ) -> OperationalAsset | None:
        with self._connect() as connection:
            row = connection.execute(query, parameters).fetchone()

        if row is None:
            return None

        return self._row_to_asset(row)

    def _get_assets(
        self,
        query: str,
        parameters: tuple[object, ...],
    ) -> list[OperationalAsset]:
        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [self._row_to_asset(row) for row in rows]

    def _row_to_asset(self, row: sqlite3.Row) -> OperationalAsset:
        return OperationalAsset(
            area_id=str(row["area_id"]),
            transformer_code=str(row["transformer_code"]),
            feeder_code=str(row["feeder_code"]),
            substation_code=str(row["substation_code"]),
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
            city=str(row["city"]),
            neighborhood=str(row["neighborhood"]),
            installed_power_kva=(
                None
                if row["installed_power_kva"] is None
                else float(row["installed_power_kva"])
            ),
            operational_status=(
                None
                if row["operational_status"] is None
                else str(row["operational_status"])
            ),
        )

    def _row_to_customer_link(self, row: sqlite3.Row) -> CustomerOperationalLink:
        return CustomerOperationalLink(
            customer_id=str(row["customer_id"]),
            area_id=str(row["area_id"]),
            transformer_code=str(row["transformer_code"]),
            feeder_code=str(row["feeder_code"]),
            substation_code=str(row["substation_code"]),
            reference_month=str(row["reference_month"]),
            customer_status=(
                None if row["customer_status"] is None else str(row["customer_status"])
            ),
            consumer_class=(
                None if row["consumer_class"] is None else str(row["consumer_class"])
            ),
        )

    def _haversine_distance_meters(
        self,
        origin_latitude: float,
        origin_longitude: float,
        target_latitude: float,
        target_longitude: float,
    ) -> float:
        earth_radius_meters = 6_371_000

        origin_latitude_rad = math.radians(origin_latitude)
        target_latitude_rad = math.radians(target_latitude)
        delta_latitude = math.radians(target_latitude - origin_latitude)
        delta_longitude = math.radians(target_longitude - origin_longitude)

        a = (
            math.sin(delta_latitude / 2) ** 2
            + math.cos(origin_latitude_rad)
            * math.cos(target_latitude_rad)
            * math.sin(delta_longitude / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return round(earth_radius_meters * c, 4)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection
