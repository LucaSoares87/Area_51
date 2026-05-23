from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from src.aerial_housing_detection.api.schemas.responses import DetectionResponse
from src.aerial_housing_detection.pipeline.orchestrator import DetectionPipeline

router = APIRouter(tags=["detection"])


@router.post(
    "/detect",
    response_model=DetectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def detect_residences(
    file: Annotated[UploadFile, File(...)],
) -> DetectionResponse:
    """Run aerial housing detection for an uploaded image."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    suffix = Path(file.filename).suffix.lower()
    if not suffix:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have an extension.",
        )

    try:
        content = await file.read()

        with NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
            temporary_file.write(content)
            temporary_path = Path(temporary_file.name)

        pipeline = DetectionPipeline()
        result = pipeline.run(temporary_path)

        return DetectionResponse(**result.to_dict())

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    finally:
        if "temporary_path" in locals() and temporary_path.exists():
            temporary_path.unlink(missing_ok=True)
