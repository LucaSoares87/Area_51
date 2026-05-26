from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from src.aerial_housing_detection.api.schemas.roof_upload import (
    RoofUploadResponse,
)
from src.aerial_housing_detection.services.roof_upload import RoofUploadService

router = APIRouter(prefix="/roof", tags=["roof"])


@router.post(
    "/upload",
    response_model=RoofUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_roof_image(
    file: Annotated[UploadFile, File()],
) -> RoofUploadResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a filename.",
        )

    content_type = file.content_type or "application/octet-stream"

    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be an image.",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image cannot be empty.",
        )

    result = RoofUploadService().analyze_upload(
        filename=file.filename,
        content_type=content_type,
        content=content,
    )

    return RoofUploadResponse(**asdict(result))
