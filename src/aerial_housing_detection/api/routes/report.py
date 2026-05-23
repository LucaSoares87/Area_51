from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from src.aerial_housing_detection.api.schemas.requests import ReportRequest
from src.aerial_housing_detection.api.schemas.responses import DetectionResponse
from src.aerial_housing_detection.pipeline.orchestrator import DetectionPipeline

router = APIRouter(tags=["report"])


@router.post("/report", response_model=DetectionResponse, status_code=status.HTTP_201_CREATED)
async def generate_report(request: ReportRequest) -> DetectionResponse:
    """Generate detection report files from a local image path."""
    image_path = Path(request.image_path)

    if not image_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image not found: {image_path}",
        )

    try:
        pipeline = DetectionPipeline()
        result = pipeline.run(image_path)
        return DetectionResponse(**result.to_dict())

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
