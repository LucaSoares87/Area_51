from dataclasses import dataclass


@dataclass(frozen=True)
class FinalSocioEnergyScore:
    area_id: str
    reference_month: str
    transformer_code: str
    feeder: str
    sector_id: str
    territory_id: str
    estimated_loss_kwh: float
    estimated_generation_kwh: float
    adjusted_loss_kwh: float
    solar_offset_ratio: float
    roof_customer_gap: int
    household_customer_gap: int
    vulnerability_ratio: float
    operational_priority_score: float
    socioenergy_priority_score: float
    final_priority_score: float
    final_risk_level: str
