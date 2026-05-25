import sqlite3
from pathlib import Path

from src.aerial_housing_detection.domain.territory import (
    CensusSector,
    OperationalTerritoryLink,
    SocialAssistanceTerritory,
    TerritorialIndicator,
)


class TerritoryRepository:
    def __init__(self, database_path: Path | str = "data/area51.db") -> None:
        self.database_path = Path(database_path)

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS census_sectors (
                    sector_id TEXT PRIMARY KEY,
                    city TEXT NOT NULL,
                    state TEXT NOT NULL,
                    neighborhood TEXT NOT NULL,
                    population INTEGER NOT NULL,
                    households INTEGER NOT NULL,
                    average_residents_per_household REAL NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS social_assistance_territories (
                    territory_id TEXT PRIMARY KEY,
                    cras_code TEXT NOT NULL,
                    cras_name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    state TEXT NOT NULL,
                    neighborhood TEXT NOT NULL,
                    assisted_families INTEGER NOT NULL,
                    vulnerable_families INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS operational_territory_links (
                    area_id TEXT PRIMARY KEY,
                    sector_id TEXT NOT NULL,
                    territory_id TEXT NOT NULL,
                    FOREIGN KEY (sector_id) REFERENCES census_sectors(sector_id),
                    FOREIGN KEY (territory_id)
                        REFERENCES social_assistance_territories(territory_id)
                )
                """
            )

    def save_census_sector(self, sector: CensusSector) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO census_sectors (
                    sector_id,
                    city,
                    state,
                    neighborhood,
                    population,
                    households,
                    average_residents_per_household
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sector_id) DO UPDATE SET
                    city = excluded.city,
                    state = excluded.state,
                    neighborhood = excluded.neighborhood,
                    population = excluded.population,
                    households = excluded.households,
                    average_residents_per_household =
                        excluded.average_residents_per_household
                """,
                (
                    sector.sector_id,
                    sector.city,
                    sector.state,
                    sector.neighborhood,
                    sector.population,
                    sector.households,
                    sector.average_residents_per_household,
                ),
            )

    def save_social_assistance_territory(
        self,
        territory: SocialAssistanceTerritory,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO social_assistance_territories (
                    territory_id,
                    cras_code,
                    cras_name,
                    city,
                    state,
                    neighborhood,
                    assisted_families,
                    vulnerable_families
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(territory_id) DO UPDATE SET
                    cras_code = excluded.cras_code,
                    cras_name = excluded.cras_name,
                    city = excluded.city,
                    state = excluded.state,
                    neighborhood = excluded.neighborhood,
                    assisted_families = excluded.assisted_families,
                    vulnerable_families = excluded.vulnerable_families
                """,
                (
                    territory.territory_id,
                    territory.cras_code,
                    territory.cras_name,
                    territory.city,
                    territory.state,
                    territory.neighborhood,
                    territory.assisted_families,
                    territory.vulnerable_families,
                ),
            )

    def save_operational_link(self, link: OperationalTerritoryLink) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO operational_territory_links (
                    area_id,
                    sector_id,
                    territory_id
                )
                VALUES (?, ?, ?)
                ON CONFLICT(area_id) DO UPDATE SET
                    sector_id = excluded.sector_id,
                    territory_id = excluded.territory_id
                """,
                (
                    link.area_id,
                    link.sector_id,
                    link.territory_id,
                ),
            )

    def build_territorial_indicator(
        self,
        area_id: str,
        estimated_roofs: int,
        customer_count: int,
    ) -> TerritorialIndicator | None:
        query = """
            SELECT
                links.area_id,
                sectors.sector_id,
                territories.territory_id,
                sectors.population,
                sectors.households,
                territories.assisted_families,
                territories.vulnerable_families
            FROM operational_territory_links links
            JOIN census_sectors sectors
                ON sectors.sector_id = links.sector_id
            JOIN social_assistance_territories territories
                ON territories.territory_id = links.territory_id
            WHERE links.area_id = ?
        """

        with self._connect() as connection:
            row = connection.execute(query, (area_id,)).fetchone()

        if row is None:
            return None

        roof_customer_gap = max(0, estimated_roofs - customer_count)
        household_customer_gap = max(0, int(row["households"]) - customer_count)
        vulnerability_ratio = self._calculate_vulnerability_ratio(
            vulnerable_families=int(row["vulnerable_families"]),
            assisted_families=int(row["assisted_families"]),
        )

        return TerritorialIndicator(
            area_id=str(row["area_id"]),
            sector_id=str(row["sector_id"]),
            territory_id=str(row["territory_id"]),
            population=int(row["population"]),
            households=int(row["households"]),
            estimated_roofs=estimated_roofs,
            customer_count=customer_count,
            assisted_families=int(row["assisted_families"]),
            vulnerable_families=int(row["vulnerable_families"]),
            roof_customer_gap=roof_customer_gap,
            household_customer_gap=household_customer_gap,
            vulnerability_ratio=vulnerability_ratio,
        )

    def _calculate_vulnerability_ratio(
        self,
        vulnerable_families: int,
        assisted_families: int,
    ) -> float:
        if assisted_families <= 0:
            return 0.0

        return round(vulnerable_families / assisted_families, 6)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection
