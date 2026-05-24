from pathlib import Path

from src.aerial_housing_detection.domain.losses import (
    LossCalculator,
    OperationalArea,
)
from src.aerial_housing_detection.storage.loss_repository import LossRepository


def test_loss_repository_saves_and_lists_records(tmp_path: Path) -> None:
    repository = LossRepository(database_path=tmp_path / "area51.db")
    repository.initialize()

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
    record = calculator.calculate_record(
        area_id=area.area_id,
        reference_month="2026-05",
        injected_energy_kwh=1000.0,
        billed_consumption_kwh=700.0,
    )

    repository.save_area(area)
    repository.save_monthly_loss_record(record)

    records = repository.list_monthly_loss_records(reference_month="2026-05")

    assert len(records) == 1
    assert records[0]["area_id"] == "area-001"
    assert records[0]["transformer_code"] == "TR-001"
    assert records[0]["estimated_loss_kwh"] == 300.0
    assert records[0]["risk_level"] == "high"
