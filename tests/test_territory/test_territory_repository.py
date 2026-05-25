from pathlib import Path

from src.aerial_housing_detection.domain.territory import (
    CensusSector,
    OperationalTerritoryLink,
    SocialAssistanceTerritory,
)
from src.aerial_housing_detection.storage.territory_repository import (
    TerritoryRepository,
)


def test_territory_repository_builds_indicator(tmp_path: Path) -> None:
    repository = TerritoryRepository(database_path=tmp_path / "area51.db")
    repository.initialize()

    sector = CensusSector(
        sector_id="sector-001",
        city="Paulista",
        state="PE",
        neighborhood="Maranguape I",
        population=480,
        households=120,
        average_residents_per_household=4.0,
    )
    territory = SocialAssistanceTerritory(
        territory_id="cras-territory-001",
        cras_code="CRAS-001",
        cras_name="CRAS Maranguape",
        city="Paulista",
        state="PE",
        neighborhood="Maranguape I",
        assisted_families=80,
        vulnerable_families=50,
    )
    link = OperationalTerritoryLink(
        area_id="area-001",
        sector_id=sector.sector_id,
        territory_id=territory.territory_id,
    )

    repository.save_census_sector(sector)
    repository.save_social_assistance_territory(territory)
    repository.save_operational_link(link)

    indicator = repository.build_territorial_indicator(
        area_id="area-001",
        estimated_roofs=135,
        customer_count=120,
    )

    assert indicator is not None
    assert indicator.area_id == "area-001"
    assert indicator.population == 480
    assert indicator.households == 120
    assert indicator.estimated_roofs == 135
    assert indicator.customer_count == 120
    assert indicator.roof_customer_gap == 15
    assert indicator.household_customer_gap == 0
    assert indicator.vulnerability_ratio == 0.625


def test_territory_repository_returns_none_without_link(tmp_path: Path) -> None:
    repository = TerritoryRepository(database_path=tmp_path / "area51.db")
    repository.initialize()

    indicator = repository.build_territorial_indicator(
        area_id="area-missing",
        estimated_roofs=100,
        customer_count=80,
    )

    assert indicator is None
