from pathlib import Path

from src.aerial_housing_detection.domain.losses import LossCalculator, OperationalArea
from src.aerial_housing_detection.domain.territory import (
    CensusSector,
    OperationalTerritoryLink,
    SocialAssistanceTerritory,
)
from src.aerial_housing_detection.services.socioenergy_analysis import (
    SocioEnergyAnalysisService,
)
from src.aerial_housing_detection.storage.loss_repository import LossRepository
from src.aerial_housing_detection.storage.territory_repository import (
    TerritoryRepository,
)


def test_socioenergy_analysis_builds_ranked_indicator(tmp_path: Path) -> None:
    database_path = tmp_path / "area51.db"

    loss_repository = LossRepository(database_path=database_path)
    territory_repository = TerritoryRepository(database_path=database_path)

    loss_repository.initialize()
    territory_repository.initialize()

    area = OperationalArea(
        area_id="area-001",
        transformer_code="TR-001",
        latitude=-7.9401,
        longitude=-34.8734,
        neighborhood="Maranguape I",
        city="Paulista",
        feeder="AL-01",
        customer_count=120,
    )
    sector = CensusSector(
        sector_id="sector-001",
        city="Paulista",
        state="PE",
        neighborhood="Maranguape I",
        population=480,
        households=130,
        average_residents_per_household=3.69,
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
        area_id=area.area_id,
        sector_id=sector.sector_id,
        territory_id=territory.territory_id,
    )

    calculator = LossCalculator()
    loss_record = calculator.calculate_record(
        area_id=area.area_id,
        reference_month="2026-05",
        injected_energy_kwh=12000.0,
        billed_consumption_kwh=8300.0,
        customer_count=area.customer_count,
        recurrence_months=2,
    )

    loss_repository.save_area(area)
    loss_repository.save_monthly_loss_record(loss_record)
    territory_repository.save_census_sector(sector)
    territory_repository.save_social_assistance_territory(territory)
    territory_repository.save_operational_link(link)

    service = SocioEnergyAnalysisService(
        loss_repository=loss_repository,
        territory_repository=territory_repository,
    )

    indicators = service.build_indicators(
        reference_month="2026-05",
        estimated_roofs_by_area={"area-001": 145},
    )

    assert len(indicators) == 1

    indicator = indicators[0]

    assert indicator.area_id == "area-001"
    assert indicator.reference_month == "2026-05"
    assert indicator.sector_id == "sector-001"
    assert indicator.territory_id == "cras-territory-001"
    assert indicator.estimated_roofs == 145
    assert indicator.customer_count == 120
    assert indicator.roof_customer_gap == 25
    assert indicator.household_customer_gap == 10
    assert indicator.vulnerability_ratio == 0.625
    assert indicator.estimated_loss_kwh == 3700.0
    assert indicator.socioenergy_priority_score > 0


def test_socioenergy_analysis_skips_area_without_territorial_link(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "area51.db"

    loss_repository = LossRepository(database_path=database_path)
    territory_repository = TerritoryRepository(database_path=database_path)

    loss_repository.initialize()
    territory_repository.initialize()

    area = OperationalArea(
        area_id="area-001",
        transformer_code="TR-001",
        latitude=-7.9401,
        longitude=-34.8734,
        neighborhood="Maranguape I",
        city="Paulista",
        feeder="AL-01",
        customer_count=120,
    )

    calculator = LossCalculator()
    loss_record = calculator.calculate_record(
        area_id=area.area_id,
        reference_month="2026-05",
        injected_energy_kwh=12000.0,
        billed_consumption_kwh=8300.0,
        customer_count=area.customer_count,
    )

    loss_repository.save_area(area)
    loss_repository.save_monthly_loss_record(loss_record)

    service = SocioEnergyAnalysisService(
        loss_repository=loss_repository,
        territory_repository=territory_repository,
    )

    indicators = service.build_indicators(
        reference_month="2026-05",
        estimated_roofs_by_area={"area-001": 145},
    )

    assert indicators == []
