from pydantic import BaseModel, Field


class LossRecordResponse(BaseModel):
    area_id: str
    transformer_code: str
    latitude: float
    longitude: float
    neighborhood: str
    city: str
    feeder: str
    customer_count: int
    reference_month: str
    injected_energy_kwh: float
    billed_consumption_kwh: float
    estimated_loss_kwh: float
    estimated_loss_percent: float
    risk_level: str
    priority_score: float


class LossRankingResponse(BaseModel):
    reference_month: str | None = None
    total_records: int
    records: list[LossRecordResponse]


class LossSummaryResponse(BaseModel):
    reference_month: str | None = None
    total_areas: int
    critical_areas: int
    high_risk_areas: int
    estimated_loss_kwh: float
    average_loss_percent: float
    top_priority_score: float


class SeedLossesRequest(BaseModel):
    reference_month: str = Field(default="2026-05")
