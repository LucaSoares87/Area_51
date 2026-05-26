from dataclasses import asdict

from fastapi import APIRouter, Query

from src.aerial_housing_detection.api.schemas.operational_search import (
    CustomerOperationalLinkResponse,
    OperationalAssetResponse,
    OperationalSearchListResponse,
    OperationalSearchResponse,
)
from src.aerial_housing_detection.services.operational_search import (
    OperationalSearchService,
)

router = APIRouter(prefix="/operational/search", tags=["operational-search"])


@router.get(
    "/customer/{customer_id}",
    response_model=OperationalSearchResponse,
)
def search_by_customer(
    customer_id: str,
    reference_month: str = Query(...),
) -> OperationalSearchResponse:
    result = OperationalSearchService().search_by_customer(
        customer_id=customer_id,
        reference_month=reference_month,
    )

    return _to_response(result)


@router.get(
    "/transformer/{transformer_code}",
    response_model=OperationalSearchResponse,
)
def search_by_transformer(transformer_code: str) -> OperationalSearchResponse:
    result = OperationalSearchService().search_by_transformer(transformer_code)

    return _to_response(result)


@router.get(
    "/feeder/{feeder_code}",
    response_model=OperationalSearchListResponse,
)
def search_by_feeder(feeder_code: str) -> OperationalSearchListResponse:
    results = OperationalSearchService().search_by_feeder(feeder_code)

    return OperationalSearchListResponse(
        search_type="feeder",
        query=feeder_code,
        total_records=len(results),
        records=[_to_response(result) for result in results],
    )


@router.get(
    "/substation/{substation_code}",
    response_model=OperationalSearchListResponse,
)
def search_by_substation(substation_code: str) -> OperationalSearchListResponse:
    results = OperationalSearchService().search_by_substation(substation_code)

    return OperationalSearchListResponse(
        search_type="substation",
        query=substation_code,
        total_records=len(results),
        records=[_to_response(result) for result in results],
    )


@router.get(
    "/coordinates",
    response_model=OperationalSearchResponse,
)
def search_by_coordinates(
    latitude: float = Query(...),
    longitude: float = Query(...),
) -> OperationalSearchResponse:
    result = OperationalSearchService().search_by_coordinates(
        latitude=latitude,
        longitude=longitude,
    )

    return _to_response(result)


def _to_response(result) -> OperationalSearchResponse:
    asset = None
    customer_link = None

    if result.asset is not None:
        asset = OperationalAssetResponse(**asdict(result.asset))

    if result.customer_link is not None:
        customer_link = CustomerOperationalLinkResponse(
            **asdict(result.customer_link)
        )

    return OperationalSearchResponse(
        search_type=result.search_type.value,
        query=result.query,
        asset=asset,
        customer_link=customer_link,
        distance_meters=result.distance_meters,
    )
