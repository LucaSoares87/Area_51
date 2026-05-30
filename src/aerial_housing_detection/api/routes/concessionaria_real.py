from fastapi import APIRouter, Query
from fastapi.responses import Response

from src.aerial_housing_detection.services.concessionaria_real_analysis import (
    ConcessionariaRealAnalysisService,
    RealConcessionariaAnalysisRequest,
)

router = APIRouter(prefix="/concessionaria/real", tags=["concessionaria-real"])


@router.get("/analysis")
def analyze_real_concessionaria_data(
    transformer_code: str | None = Query(default=None),
    latitude: float | None = Query(default=None),
    longitude: float | None = Query(default=None),
) -> dict:
    service = ConcessionariaRealAnalysisService()
    return service.analyze(
        RealConcessionariaAnalysisRequest(
            transformer_code=transformer_code,
            latitude=latitude,
            longitude=longitude,
        )
    )


@router.get("/export.csv")
def export_real_concessionaria_analysis(
    transformer_code: str | None = Query(default=None),
    latitude: float | None = Query(default=None),
    longitude: float | None = Query(default=None),
) -> Response:
    service = ConcessionariaRealAnalysisService()
    content = service.export_csv(
        RealConcessionariaAnalysisRequest(
            transformer_code=transformer_code,
            latitude=latitude,
            longitude=longitude,
        )
    )

    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                "attachment; filename=concessionaria_real_analysis.csv"
            )
        },
    )
