from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy")
    service: str = Field(default="aerial_housing_detection")
    version: str


class DetectionResponse(BaseModel):
    """Detection API response."""

    analysis_id: str
    estimated_residences: int
    roof_count: int
    confidence_score: float
    csv_report_path: str
    html_map_path: str


class ErrorResponse(BaseModel):
    """Standard API error response."""

    detail: str
