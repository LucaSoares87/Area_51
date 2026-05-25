import sqlite3
from pathlib import Path

from src.aerial_housing_detection.domain.losses import (
    MonthlyLossRecord,
    OperationalArea,
)


class LossRepository:
    def __init__(self, database_path: Path | str = "data/area51.db") -> None:
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS operational_areas (
                    area_id TEXT PRIMARY KEY,
                    transformer_code TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    neighborhood TEXT NOT NULL,
                    city TEXT NOT NULL,
                    feeder TEXT NOT NULL,
                    customer_count INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS monthly_loss_records (
                    area_id TEXT NOT NULL,
                    reference_month TEXT NOT NULL,
                    injected_energy_kwh REAL NOT NULL,
                    billed_consumption_kwh REAL NOT NULL,
                    estimated_loss_kwh REAL NOT NULL,
                    estimated_loss_percent REAL NOT NULL,
                    risk_level TEXT NOT NULL,
                    priority_score REAL NOT NULL,
                    PRIMARY KEY (area_id, reference_month),
                    FOREIGN KEY (area_id) REFERENCES operational_areas(area_id)
                )
                """
            )

    def save_area(self, area: OperationalArea) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO operational_areas (
                    area_id,
                    transformer_code,
                    latitude,
                    longitude,
                    neighborhood,
                    city,
                    feeder,
                    customer_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(area_id) DO UPDATE SET
                    transformer_code = excluded.transformer_code,
                    latitude = excluded.latitude,
                    longitude = excluded.longitude,
                    neighborhood = excluded.neighborhood,
                    city = excluded.city,
                    feeder = excluded.feeder,
                    customer_count = excluded.customer_count
                """,
                (
                    area.area_id,
                    area.transformer_code,
                    area.latitude,
                    area.longitude,
                    area.neighborhood,
                    area.city,
                    area.feeder,
                    area.customer_count,
                ),
            )

    def save_monthly_loss_record(self, record: MonthlyLossRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO monthly_loss_records (
                    area_id,
                    reference_month,
                    injected_energy_kwh,
                    billed_consumption_kwh,
                    estimated_loss_kwh,
                    estimated_loss_percent,
                    risk_level,
                    priority_score
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(area_id, reference_month) DO UPDATE SET
                    injected_energy_kwh = excluded.injected_energy_kwh,
                    billed_consumption_kwh = excluded.billed_consumption_kwh,
                    estimated_loss_kwh = excluded.estimated_loss_kwh,
                    estimated_loss_percent = excluded.estimated_loss_percent,
                    risk_level = excluded.risk_level,
                    priority_score = excluded.priority_score
                """,
                (
                    record.area_id,
                    record.reference_month,
                    record.injected_energy_kwh,
                    record.billed_consumption_kwh,
                    record.estimated_loss_kwh,
                    record.estimated_loss_percent,
                    record.risk_level.value,
                    record.priority_score,
                ),
            )

    def list_monthly_loss_records(
        self,
        reference_month: str | None = None,
    ) -> list[dict[str, object]]:
        query = """
            SELECT
                areas.area_id,
                areas.transformer_code,
                areas.latitude,
                areas.longitude,
                areas.neighborhood,
                areas.city,
                areas.feeder,
                areas.customer_count,
                losses.reference_month,
                losses.injected_energy_kwh,
                losses.billed_consumption_kwh,
                losses.estimated_loss_kwh,
                losses.estimated_loss_percent,
                losses.risk_level,
                losses.priority_score
            FROM monthly_loss_records losses
            JOIN operational_areas areas
                ON areas.area_id = losses.area_id
        """
        parameters: tuple[object, ...] = ()

        if reference_month:
            query += " WHERE losses.reference_month = ?"
            parameters = (reference_month,)

        query += " ORDER BY losses.priority_score DESC"

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [dict(row) for row in rows]

    def count_recent_loss_recurrence(
        self,
        area_id: str,
        reference_month: str,
        minimum_loss_percent: float = 0.1,
        max_months: int = 6,
    ) -> int:
        query = """
            SELECT COUNT(*) AS recurrence_count
            FROM (
                SELECT estimated_loss_percent
                FROM monthly_loss_records
                WHERE area_id = ?
                  AND reference_month <= ?
                ORDER BY reference_month DESC
                LIMIT ?
            ) recent_losses
            WHERE estimated_loss_percent >= ?
        """

        with self._connect() as connection:
            row = connection.execute(
                query,
                (
                    area_id,
                    reference_month,
                    max_months,
                    minimum_loss_percent,
                ),
            ).fetchone()

        if row is None:
            return 0

        return int(row["recurrence_count"])

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection
