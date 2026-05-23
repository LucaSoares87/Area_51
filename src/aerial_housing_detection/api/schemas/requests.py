from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    """Request body for report generation."""

    image_path: str = Field(
        min_length=1,
        description="Local image path used to generate a new report.",
    )
