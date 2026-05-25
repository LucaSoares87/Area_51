from pathlib import Path

from src.aerial_housing_detection.domain.losses import LossCalculator, OperationalArea
from src.aerial_housing_detection.domain.solar import SolarAreaEstimate
from src.aerial_housing_detection.domain.territory import (
    CensusSector,
    OperationalTerritoryLink,
    SocialAssistanceTerritory,
)
from src.aerial_housing_detection.services.final_socioenergy_score import (
    FinalSocioEnergyScoreService,
)
from src.aerial_housing_detection.services.grid_aggregation import GridAggregationService
from src.aerial_housing_detection.services.socioenergy_analysis import (
    SocioEnergyAnalysisService,
)
from src.aerial_housing_detection.storage.loss_repository import LossRepository
from src.aerial_housing_detection.storage.solar_repository import SolarRepository
from src.aerial_housing_detection.storage.territory_repository import (
    TerritoryRepository,
)


def test_final_socioenergy_score_builds_ranked_score(tmp_path: Path) -> None:
    database_path = tmp_path / "area51.db"

    loss_repository = LossRepository(database_path=database_path)
    territory_repository = TerritoryRepository(database_path=database_path)
    solar_repository = SolarRepository(database_path=database_path)

    loss_repository.initialize()
    territory_repository.initialize()
    solar_repository.initialize()

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
    loss_record = LossCalculator().calculate_record(
        area_id=area.area_id,
        reference_month="2026-05",
        injected_energy_kwh=12000.0,
        billed_consumption_kwh=8300.0,
        customer_count=area.customer_count,
        recurrence_months=2,
    )
    solar_estimate = SolarAreaEstimate(
        area_id=area.area_id,
        reference_month="2026-05",
        solar_panel_count=18,
        estimated_solar_area_m2=72.0,
        estimated_generation_kwh=950.0,
        confidence_score=0.86,
    )

    loss_repository.save_area(area)
    loss_repository.save_monthly_loss_record(loss_record)
    territory_repository.save_census_sector(sector)
    territory_repository.save_social_assistance_territory(territory)
    territory_repository.save_operational_link(link)
    solar_repository.save_estimate(solar_estimate)

    socioenergy_service = SocioEnergyAnalysisService(
        loss_repository=loss_repository,
        territory_repository=territory_repository,
    )
    grid_aggregation_service = GridAggregationService(
        loss_repository=loss_repository,
        solar_repository=solar_repository,
    )
    service = FinalSocioEnergyScoreService(
        socioenergy_service=socioenergy_service,
        grid_aggregation_service=grid_aggregation_service,
    )

    scores = service.build_scores(
        reference_month="2026-05",
        estimated_roofs_by_area={"area-001": 145},
    )

    assert len(scores) == 1

    score = scores[0]

    assert score.area_id == "area-001"
    assert score.transformer_code == "TR-001"
    assert score.feeder == "AL-01"
    assert score.sector_id == "sector-001"
    assert score.territory_id == "cras-territory-001"
    assert score.estimated_loss_kwh == 3700.0
    assert score.estimated_generation_kwh == 950.0
    assert score.adjusted_loss_kwh == 2750.0
    assert score.solar_offset_ratio == 0.256757
    assert score.final_priority_score > 0
    assert score.final_risk_level in {"low", "medium", "high", "critical"}


def test_final_socioenergy_score_returns_empty_without_links(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "area51.db"

    loss_repository = LossRepository(database_path=database_path)
    territory_repository = TerritoryRepository(database_path=database_path)
    solar_repository = SolarRepository(database_path=database_path)

    loss_repository.initialize()
    territory_repository.initialize()
    solar_repository.initialize()

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
    loss_record = LossCalculator().calculate_record(
        area_id=area.area_id,
        reference_month="2026-05",
        injected_energy_kwh=12000.0,
        billed_consumption_kwh=8300.0,
        customer_count=area.customer_count,
    )

    loss_repository.save_area(area)
    loss_repository.save_monthly_loss_record(loss_record)

    socioenergy_service = SocioEnergyAnalysisService(
        loss_repository=loss_repository,
        territory_repository=territory_repository,
    )
    grid_aggregation_service = GridAggregationService(
        loss_repository=loss_repository,
        solar_repository=solar_repository,
    )
    service = FinalSocioEnergyScoreService(
        socioenergy_service=socioenergy_service,
        grid_aggregation_service=grid_aggregation_service,
    )

    scores = service.build_scores(
        reference_month="2026-05",
        estimated_roofs_by_area={"area-001": 145},
    )

    assert scores == []
