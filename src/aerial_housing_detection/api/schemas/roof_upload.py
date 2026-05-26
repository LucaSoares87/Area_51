from pydantic import BaseModel


class RoofUploadResponse(BaseModel):
    analysis_id: str
    filename: str
    content_type: str
    estimated_roofs: int
    confidence_score: float
    status: str
