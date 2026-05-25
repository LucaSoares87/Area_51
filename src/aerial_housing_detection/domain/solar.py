from dataclasses import dataclass


@dataclass(frozen=True)
class SolarAreaEstimate:
    area_id: str
    reference_month: str
    solar_panel_count: int
    estimated_solar_area_m2: float
    estimated_generation_kwh: float
    confidence_score: float


@dataclass(frozen=True)
class SolarAdjustedLoss:
    area_id: str
    reference_month: str
    estimated_loss_kwh: float
    estimated_generation_kwh: float
    adjusted_loss_kwh: float
    solar_offset_ratio: float
