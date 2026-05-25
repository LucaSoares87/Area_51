from pathlib import Path

from src.aerial_housing_detection.domain.losses import LossCalculator, OperationalArea
from src.aerial_housing_detection.domain.solar import SolarAreaEstimate
from src.aerial_housing_detection.services.solar_balance import SolarBalanceService
from src.aerial_housing_detection.storage.loss_repository import LossRepository
from src.aerial_housing_detection.storage.solar_repository import SolarRepository


def test_solar_balance_builds_adjusted_loss(tmp_path: Path) -> None:
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
        area_id=area.area_id,
        reference_month="2026-05",
        solar_panel_count=18,
        estimated_solar_area_m2=72.0,
        estimated_generation_kwh=950.0,
        confidence_score=0.86,
    )

    loss_repository.save_area(area)
    loss_repository.save_monthly_loss_record(loss_record)
    solar_repository.save_estimate(solar_estimate)

    service = SolarBalanceService(
        loss_repository=loss_repository,
        solar_repository=solar_repository,
    )

    adjusted_losses = service.build_adjusted_losses(reference_month="2026-05")

    assert len(adjusted_losses) == 1

    adjusted_loss = adjusted_losses[0]

    assert adjusted_loss.area_id == "area-001"
    assert adjusted_loss.estimated_loss_kwh == 3700.0
    assert adjusted_loss.estimated_generation_kwh == 950.0
    assert adjusted_loss.adjusted_loss_kwh == 2750.0
    assert adjusted_loss.solar_offset_ratio == 0.256757


def test_solar_balance_uses_zero_generation_when_estimate_is_missing(
    tmp_path: Path,
) -> None:
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

    loss_repository.save_area(area)
    loss_repository.save_monthly_loss_record(loss_record)

    service = SolarBalanceService(
        loss_repository=loss_repository,
        solar_repository=solar_repository,
    )

    adjusted_losses = service.build_adjusted_losses(reference_month="2026-05")

    assert len(adjusted_losses) == 1

    adjusted_loss = adjusted_losses[0]

    assert adjusted_loss.estimated_generation_kwh == 0.0
    assert adjusted_loss.adjusted_loss_kwh == 3700.0
    assert adjusted_loss.solar_offset_ratio == 0.0
