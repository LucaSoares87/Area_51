from pathlib import Path

from src.aerial_housing_detection.domain.losses import LossCalculator, OperationalArea
from src.aerial_housing_detection.domain.solar import SolarAreaEstimate
from src.aerial_housing_detection.services.grid_aggregation import GridAggregationService
from src.aerial_housing_detection.storage.loss_repository import LossRepository
from src.aerial_housing_detection.storage.solar_repository import SolarRepository


def test_grid_aggregation_builds_transformer_summaries(tmp_path: Path) -> None:
    database_path = tmp_path / "area51.db"
    loss_repository = LossRepository(database_path=database_path)
    solar_repository = SolarRepository(database_path=database_path)

    loss_repository.initialize()
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
    solar_estimate = SolarAreaEstimate(
        area_id="area-001",
        reference_month="2026-05",
        solar_panel_count=18,
        estimated_solar_area_m2=72.0,
        estimated_generation_kwh=950.0,
        confidence_score=0.86,
    )

    loss_repository.save_area(area)
    loss_repository.save_monthly_loss_record(loss_record)
    solar_repository.save_estimate(solar_estimate)

    service = GridAggregationService(
        loss_repository=loss_repository,
        solar_repository=solar_repository,
    )

    summaries = service.build_transformer_summaries(reference_month="2026-05")

    assert len(summaries) == 1

    summary = summaries[0]

    assert summary.area_id == "area-001"
    assert summary.transformer_code == "TR-001"
    assert summary.feeder == "AL-01"
    assert summary.estimated_loss_kwh == 3700.0
    assert summary.estimated_generation_kwh == 950.0
    assert summary.adjusted_loss_kwh == 2750.0
    assert summary.solar_offset_ratio == 0.256757


def test_grid_aggregation_builds_feeder_summaries(tmp_path: Path) -> None:
    database_path = tmp_path / "area51.db"
    loss_repository = LossRepository(database_path=database_path)
    solar_repository = SolarRepository(database_path=database_path)

    loss_repository.initialize()
    solar_repository.initialize()

    areas = [
        OperationalArea(
            area_id="area-001",
            transformer_code="TR-001",
            latitude=-7.9401,
            longitude=-34.8734,
            neighborhood="Maranguape I",
            city="Paulista",
            feeder="AL-01",
            customer_count=120,
        ),
        OperationalArea(
            area_id="area-002",
            transformer_code="TR-002",
            latitude=-7.9512,
            longitude=-34.8821,
            neighborhood="Janga",
            city="Paulista",
            feeder="AL-01",
            customer_count=98,
        ),
    ]

    calculator = LossCalculator()

    for area in areas:
        record = calculator.calculate_record(
            area_id=area.area_id,
            reference_month="2026-05",
            injected_energy_kwh=12000.0,
            billed_consumption_kwh=8300.0,
            customer_count=area.customer_count,
        )
        loss_repository.save_area(area)
        loss_repository.save_monthly_loss_record(record)

    solar_repository.save_estimate(
        SolarAreaEstimate(
            area_id="area-001",
            reference_month="2026-05",
            solar_panel_count=18,
            estimated_solar_area_m2=72.0,
            estimated_generation_kwh=950.0,
            confidence_score=0.86,
        )
    )
    solar_repository.save_estimate(
        SolarAreaEstimate(
            area_id="area-002",
            reference_month="2026-05",
            solar_panel_count=4,
            estimated_solar_area_m2=16.0,
            estimated_generation_kwh=210.0,
            confidence_score=0.74,
        )
    )

    service = GridAggregationService(
        loss_repository=loss_repository,
        solar_repository=solar_repository,
    )

    summaries = service.build_feeder_summaries(reference_month="2026-05")

    assert len(summaries) == 1

    summary = summaries[0]

    assert summary.feeder == "AL-01"
    assert summary.transformer_count == 2
    assert summary.customer_count == 218
    assert summary.estimated_loss_kwh == 7400.0
    assert summary.estimated_generation_kwh == 1160.0
    assert summary.adjusted_loss_kwh == 6240.0
    assert summary.average_solar_offset_ratio > 0
