from dataclasses import asdict

from fastapi import APIRouter

from src.aerial_housing_detection.api.schemas.socioenergy import (
    SocioEnergyAnalysisRequest,
    SocioEnergyAnalysisResponse,
    SocioEnergyIndicatorResponse,
)
from src.aerial_housing_detection.services.socioenergy_analysis import (
    SocioEnergyAnalysisService,
)

router = APIRouter(prefix="/socioenergy", tags=["socioenergy"])


@router.post("/analysis", response_model=SocioEnergyAnalysisResponse)
def build_socioenergy_analysis(
    request: SocioEnergyAnalysisRequest,
) -> SocioEnergyAnalysisResponse:
    estimated_roofs_by_area = {
        item.area_id: item.estimated_roofs for item in request.estimated_roofs_by_area
    }

    service = SocioEnergyAnalysisService()
    indicators = service.build_indicators(
        reference_month=request.reference_month,
        estimated_roofs_by_area=estimated_roofs_by_area,
    )

    records = [
        SocioEnergyIndicatorResponse(**asdict(indicator))
        for indicator in indicators
    ]

    return SocioEnergyAnalysisResponse(
        reference_month=request.reference_month,
        total_records=len(records),
        records=records,
    )
