from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import Optional

from src.auth.dependencies import get_current_user, require_analyst
from src.auth.models import User
from src.detect.config import detect_settings
from src.detect.analysis_service import AnalysisService
from src.detect.models import AnalysisResult

router = APIRouter(prefix="/api/v1/detect", tags=["detection"])

analysis_service = AnalysisService()


@router.post("/analyze", response_model=AnalysisResult, status_code=201)
async def analyze_image(
    file: UploadFile = File(...),
    cross_reference: bool = False,
    user: User = Depends(require_analyst),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome do arquivo ausente",
        )

    suffix = f".{file.filename.rsplit('.', 1)[-1].lower()}" if "." in file.filename else ""
    if suffix not in detect_settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Extensao nao permitida. Use: {detect_settings.allowed_extensions}",
        )

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > detect_settings.max_image_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo excede {detect_settings.max_image_size_mb}MB",
        )

    file_path = await analysis_service.image_processor.save_upload(content, file.filename)
    result = await analysis_service.analyze(file_path, user.username, cross_reference)
    return result


@router.post("/analyze/batch", response_model=list[AnalysisResult], status_code=201)
async def analyze_batch(
    files: list[UploadFile] = File(...),
    user: User = Depends(require_analyst),
):
    if len(files) > detect_settings.batch_max_images:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Batch excede o limite de {detect_settings.batch_max_images} imagens",
        )

    paths = []
    for file in files:
        content = await file.read()
        path = await analysis_service.image_processor.save_upload(content, file.filename or "unknown.jpg")
        paths.append(path)

    results = await analysis_service.analyze_batch(paths, user.username)
    return results


@router.get("/results", response_model=list[AnalysisResult])
async def list_results(
    limit: int = 50,
    user: User = Depends(get_current_user),
):
    return analysis_service.list_results(requester=user.username, limit=limit)


@router.get("/results/{analysis_id}", response_model=AnalysisResult)
async def get_result(
    analysis_id: str,
    user: User = Depends(get_current_user),
):
    result = analysis_service.get_result(analysis_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analise nao encontrada",
        )
    return result


@router.get("/config")
async def get_detection_config(user: User = Depends(require_analyst)):
    return {
        "tile_size": detect_settings.tile_size,
        "tile_overlap": detect_settings.tile_overlap,
        "confidence_threshold": detect_settings.confidence_threshold,
        "nms_iou_threshold": detect_settings.nms_iou_threshold,
        "max_image_size_mb": detect_settings.max_image_size_mb,
        "allowed_extensions": detect_settings.allowed_extensions,
        "batch_max_images": detect_settings.batch_max_images,
        "mock_inference": detect_settings.mock_inference,
        "cross_reference_enabled": detect_settings.cross_reference_enabled,
    }
