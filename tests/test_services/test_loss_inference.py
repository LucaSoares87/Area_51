from src.aerial_housing_detection.services.loss_inference import (
    LossInferenceInput,
    LossInferenceService,
)


def test_loss_inference_calculates_adjusted_loss() -> None:
    service = LossInferenceService()

    result = service.infer(
        LossInferenceInput(
            transformer_input_kwh=176450,
            billed_consumption_kwh=138000,
            gd_injected_kwh=12600,
            estimated_houses=74,
        )
    )

    assert result.energy_balance.estimated_loss_kwh == 25850
    assert round(result.energy_balance.estimated_loss_percent, 2) == 14.65
    assert round(result.energy_balance.estimated_loss_per_house_kwh or 0, 2) == 349.32
    assert result.priority == "Alta"
    assert result.score >= 70


def test_loss_inference_caps_negative_loss_at_zero() -> None:
    service = LossInferenceService()

    result = service.infer(
        LossInferenceInput(
            transformer_input_kwh=1000,
            billed_consumption_kwh=1200,
            gd_injected_kwh=200,
            estimated_houses=10,
        )
    )

    assert result.energy_balance.estimated_loss_kwh == 0
    assert result.energy_balance.estimated_loss_percent == 0
    assert result.priority == "Baixa"
