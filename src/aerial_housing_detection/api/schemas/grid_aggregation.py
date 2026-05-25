from pydantic import BaseModel


class TransformerLossSummaryResponse(BaseModel):
    area_id: str
    transformer_code: str
    feeder: str
    reference_month: str
    customer_count: int
    estimated_loss_kwh: float
    estimated_generation_kwh: float
    adjusted_loss_kwh: float
    estimated_loss_percent: float
    solar_offset_ratio: float
    priority_score: float
    risk_level: str


class TransformerLossRankingResponse(BaseModel):
    reference_month: str
    total_records: int
    records: list[TransformerLossSummaryResponse]


class FeederLossSummaryResponse(BaseModel):
    feeder: str
    reference_month: str
    transformer_count: int
    customer_count: int
    estimated_loss_kwh: float
    estimated_generation_kwh: float
    adjusted_loss_kwh: float
    average_loss_percent: float
    average_solar_offset_ratio: float
    average_priority_score: float
    critical_transformers: int
    high_risk_transformers: int


class FeederLossRankingResponse(BaseModel):
    reference_month: str
    total_records: int
    records: list[FeederLossSummaryResponse]
