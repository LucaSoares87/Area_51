from dataclasses import dataclass


@dataclass(frozen=True)
class SocioEnergyIndicator:
    area_id: str
    reference_month: str
    sector_id: str
    territory_id: str
    population: int
    households: int
    estimated_roofs: int
    customer_count: int
    roof_customer_gap: int
    household_customer_gap: int
    assisted_families: int
    vulnerable_families: int
    vulnerability_ratio: float
    estimated_loss_kwh: float
    estimated_loss_percent: float
    operational_risk_level: str
    operational_priority_score: float
    socioenergy_priority_score: float
