from pydantic import BaseModel, Field


class EstimatedRoofsInput(BaseModel):
    area_id: str
    estimated_roofs: int = Field(ge=0)


class SocioEnergyAnalysisRequest(BaseModel):
    reference_month: str
    estimated_roofs_by_area: list[EstimatedRoofsInput]


class SocioEnergyIndicatorResponse(BaseModel):
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


class SocioEnergyAnalysisResponse(BaseModel):
    reference_month: str
    total_records: int
    records: list[SocioEnergyIndicatorResponse]
