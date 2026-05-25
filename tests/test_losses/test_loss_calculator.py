from src.aerial_housing_detection.domain.losses import (
    LossCalculator,
    LossRiskLevel,
    OperationalRiskInput,
    OperationalRiskScorer,
)


def test_loss_calculator_computes_loss_values() -> None:
    calculator = LossCalculator()

    record = calculator.calculate_record(
        area_id="area-001",
        reference_month="2026-05",
        injected_energy_kwh=1000.0,
        billed_consumption_kwh=750.0,
        customer_count=120,
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
        customer_count=120,
    )

    assert record.estimated_loss_kwh == 0.0
    assert record.estimated_loss_percent == 0.0
    assert record.risk_level == LossRiskLevel.LOW


def test_operational_risk_scorer_increases_with_recurrence() -> None:
    scorer = OperationalRiskScorer()

    low_recurrence_score = scorer.calculate_score(
        OperationalRiskInput(
            estimated_loss_kwh=1000.0,
            estimated_loss_percent=0.2,
            customer_count=100,
            recurrence_months=1,
        )
    )
    high_recurrence_score = scorer.calculate_score(
        OperationalRiskInput(
            estimated_loss_kwh=1000.0,
            estimated_loss_percent=0.2,
            customer_count=100,
            recurrence_months=3,
        )
    )

    assert high_recurrence_score > low_recurrence_score


def test_operational_risk_scorer_caps_score_at_100() -> None:
    scorer = OperationalRiskScorer()

    score = scorer.calculate_score(
        OperationalRiskInput(
            estimated_loss_kwh=50000.0,
            estimated_loss_percent=0.8,
            customer_count=1000,
            recurrence_months=12,
        )
    )

    assert score == 100.0
