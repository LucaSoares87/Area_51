from dataclasses import asdict

from fastapi import APIRouter, Query

from src.aerial_housing_detection.api.schemas.grid_aggregation import (
    FeederLossRankingResponse,
    FeederLossSummaryResponse,
    TransformerLossRankingResponse,
    TransformerLossSummaryResponse,
)
from src.aerial_housing_detection.services.grid_aggregation import (
    GridAggregationService,
)

router = APIRouter(prefix="/grid", tags=["grid"])


@router.get(
    "/transformers/ranking",
    response_model=TransformerLossRankingResponse,
)
def get_transformer_loss_ranking(
    reference_month: str = Query(...),
    limit: int = Query(default=20, ge=1, le=100),
) -> TransformerLossRankingResponse:
    service = GridAggregationService()
    summaries = service.build_transformer_summaries(
        reference_month=reference_month,
    )
    limited_summaries = summaries[:limit]

    return TransformerLossRankingResponse(
        reference_month=reference_month,
        total_records=len(summaries),
        records=[
            TransformerLossSummaryResponse(**asdict(summary))
            for summary in limited_summaries
        ],
    )


@router.get(
    "/feeders/ranking",
    response_model=FeederLossRankingResponse,
)
def get_feeder_loss_ranking(
    reference_month: str = Query(...),
    limit: int = Query(default=20, ge=1, le=100),
) -> FeederLossRankingResponse:
    service = GridAggregationService()
    summaries = service.build_feeder_summaries(
        reference_month=reference_month,
    )
    limited_summaries = summaries[:limit]

    return FeederLossRankingResponse(
        reference_month=reference_month,
        total_records=len(summaries),
        records=[
            FeederLossSummaryResponse(**asdict(summary))
            for summary in limited_summaries
        ],
    )
