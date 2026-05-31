from fastapi import APIRouter, Query
from fastapi.responses import Response

from src.aerial_housing_detection.services.operational_feature_store import (
    OperationalFeatureStore,
)

router = APIRouter(prefix="/features/operational", tags=["operational-features"])


@router.get("/transformer/{transformer_code}")
def get_transformer_operational_features(transformer_code: str) -> dict:
    store = OperationalFeatureStore()
    return store.get_transformer_features(transformer_code)


@router.get("/ranking")
def get_operational_features_ranking(
    limit: int = Query(default=50, ge=1, le=500),
) -> dict:
    store = OperationalFeatureStore()
    return store.get_ranking(limit=limit)


@router.get("/export.csv")
def export_operational_features() -> Response:
    store = OperationalFeatureStore()
    content = store.export_csv()

    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                "attachment; filename=operational_features.csv"
            )
        },
    )
