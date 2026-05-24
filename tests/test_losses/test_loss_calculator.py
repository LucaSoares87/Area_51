from src.aerial_housing_detection.domain.losses import LossCalculator, LossRiskLevel


def test_loss_calculator_computes_loss_values() -> None:
    calculator = LossCalculator()

    record = calculator.calculate_record(
        area_id="area-001",
        reference_month="2026-05",
        injected_energy_kwh=1000.0,
        billed_consumption_kwh=750.0,
    )

    assert record.estimated_loss_kwh == 250.0
    assert record.estimated_loss_percent == 0.25
    assert record.risk_level == LossRiskLevel.HIGH
    assert record.priority_score > 0


def test_loss_calculator_handles_zero_injected_energy() -> None:
    calculator = LossCalculator()

    record = calculator.calculate_record(
        area_id="area-001",
        reference_month="2026-05",
        injected_energy_kwh=0.0,
        billed_consumption_kwh=750.0,
    )

    assert record.estimated_loss_kwh == 0.0
    assert record.estimated_loss_percent == 0.0
    assert record.risk_level == LossRiskLevel.LOW
