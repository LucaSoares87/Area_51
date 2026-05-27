from dataclasses import dataclass


@dataclass(frozen=True)
class EnergyBalanceInput:
    transformer_input_kwh: float
    billed_consumption_kwh: float
    gd_injected_kwh: float = 0.0
    technical_loss_kwh: float = 0.0
    estimated_houses: int | None = None


@dataclass(frozen=True)
class EnergyBalanceResult:
    transformer_input_kwh: float
    billed_consumption_kwh: float
    gd_injected_kwh: float
    technical_loss_kwh: float
    estimated_loss_kwh: float
    estimated_loss_percent: float
    estimated_loss_per_house_kwh: float | None


def calculate_energy_balance(payload: EnergyBalanceInput) -> EnergyBalanceResult:
    transformer_input = max(payload.transformer_input_kwh, 0.0)
    billed_consumption = max(payload.billed_consumption_kwh, 0.0)
    gd_injected = max(payload.gd_injected_kwh, 0.0)
    technical_loss = max(payload.technical_loss_kwh, 0.0)

    estimated_loss = transformer_input - billed_consumption
    estimated_loss -= gd_injected
    estimated_loss -= technical_loss
    estimated_loss = max(estimated_loss, 0.0)

    estimated_loss_percent = 0.0
    if transformer_input > 0:
        estimated_loss_percent = (estimated_loss / transformer_input) * 100

    estimated_loss_per_house = None
    if payload.estimated_houses and payload.estimated_houses > 0:
        estimated_loss_per_house = estimated_loss / payload.estimated_houses

    return EnergyBalanceResult(
        transformer_input_kwh=transformer_input,
        billed_consumption_kwh=billed_consumption,
        gd_injected_kwh=gd_injected,
        technical_loss_kwh=technical_loss,
        estimated_loss_kwh=estimated_loss,
        estimated_loss_percent=estimated_loss_percent,
        estimated_loss_per_house_kwh=estimated_loss_per_house,
    )
