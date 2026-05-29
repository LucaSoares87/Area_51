from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import FileResponse, Response

from scripts.generate_realistic_operational_map import build_map_html
from src.aerial_housing_detection.services.demo_realistic_analysis import (
    RealisticAnalysisRequest,
    RealisticDemoAnalysisService,
)

REPORTS_DIR = Path("reports")
MAP_PATH = REPORTS_DIR / "realistic_operational_map.html"

router = APIRouter(prefix="/demo/realistic", tags=["demo-realistic"])


@router.get("/analysis")
def get_realistic_analysis(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_meters: int = Query(600),
) -> dict:
    service = RealisticDemoAnalysisService()

    return service.analyze(
        RealisticAnalysisRequest(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
        )
    )


@router.get("/map")
def get_realistic_map(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_meters: int = Query(600),
) -> Response:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    service = RealisticDemoAnalysisService()
    analysis = service.analyze(
        RealisticAnalysisRequest(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
        )
    )
    MAP_PATH.write_text(build_map_html(analysis), encoding="utf-8")

    return FileResponse(MAP_PATH)


@router.get("/export.csv")
def export_realistic_analysis_csv(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_meters: int = Query(600),
) -> Response:
    service = RealisticDemoAnalysisService()
    content = service.export_csv(
        RealisticAnalysisRequest(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius_meters,
        )
    )

    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=area51_realistic_analysis.csv"
        },
    )