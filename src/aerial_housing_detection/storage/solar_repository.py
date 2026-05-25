import sqlite3
from pathlib import Path

from src.aerial_housing_detection.domain.solar import SolarAreaEstimate


class SolarRepository:
    def __init__(self, database_path: Path | str = "data/area51.db") -> None:
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS solar_area_estimates (
                    area_id TEXT NOT NULL,
                    reference_month TEXT NOT NULL,
                    solar_panel_count INTEGER NOT NULL,
                    estimated_solar_area_m2 REAL NOT NULL,
                    estimated_generation_kwh REAL NOT NULL,
                    confidence_score REAL NOT NULL,
                    PRIMARY KEY (area_id, reference_month)
                )
                """
            )

    def save_estimate(self, estimate: SolarAreaEstimate) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO solar_area_estimates (
                    area_id,
                    reference_month,
                    solar_panel_count,
                    estimated_solar_area_m2,
                    estimated_generation_kwh,
                    confidence_score
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(area_id, reference_month) DO UPDATE SET
                    solar_panel_count = excluded.solar_panel_count,
                    estimated_solar_area_m2 = excluded.estimated_solar_area_m2,
                    estimated_generation_kwh = excluded.estimated_generation_kwh,
                    confidence_score = excluded.confidence_score
                """,
                (
                    estimate.area_id,
                    estimate.reference_month,
                    estimate.solar_panel_count,
                    estimate.estimated_solar_area_m2,
                    estimate.estimated_generation_kwh,
                    estimate.confidence_score,
                ),
            )

    def get_estimate(
        self,
        area_id: str,
        reference_month: str,
    ) -> dict[str, object] | None:
        query = """
            SELECT
                area_id,
                reference_month,
                solar_panel_count,
                estimated_solar_area_m2,
                estimated_generation_kwh,
                confidence_score
            FROM solar_area_estimates
            WHERE area_id = ?
              AND reference_month = ?
        """

        with self._connect() as connection:
            row = connection.execute(
                query,
                (
                    area_id,
                    reference_month,
                ),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def list_estimates(
        self,
        reference_month: str | None = None,
    ) -> list[dict[str, object]]:
        query = """
            SELECT
                area_id,
                reference_month,
                solar_panel_count,
                estimated_solar_area_m2,
                estimated_generation_kwh,
                confidence_score
            FROM solar_area_estimates
        """
        parameters: tuple[object, ...] = ()

        if reference_month:
            query += " WHERE reference_month = ?"
            parameters = (reference_month,)

        query += " ORDER BY estimated_generation_kwh DESC"

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [dict(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection
