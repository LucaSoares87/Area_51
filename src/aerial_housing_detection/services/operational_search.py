from src.aerial_housing_detection.domain.operational_search import (
    OperationalSearchResult,
    OperationalSearchType,
)
from src.aerial_housing_detection.storage.operational_repository import (
    OperationalRepository,
)


class OperationalSearchService:
    def __init__(self, repository: OperationalRepository | None = None) -> None:
        self.repository = repository or OperationalRepository()

    def search_by_customer(
        self,
        customer_id: str,
        reference_month: str,
    ) -> OperationalSearchResult:
        self.repository.initialize()

        link = self.repository.get_customer_link(
            customer_id=customer_id,
            reference_month=reference_month,
        )

        if link is None:
            return OperationalSearchResult(
                search_type=OperationalSearchType.CUSTOMER,
                query=customer_id,
                asset=None,
                customer_link=None,
            )

        asset = self.repository.get_asset_by_area(link.area_id)

        return OperationalSearchResult(
            search_type=OperationalSearchType.CUSTOMER,
            query=customer_id,
            asset=asset,
            customer_link=link,
        )

    def search_by_transformer(
        self,
        transformer_code: str,
    ) -> OperationalSearchResult:
        self.repository.initialize()
        asset = self.repository.get_asset_by_transformer(transformer_code)

        return OperationalSearchResult(
            search_type=OperationalSearchType.TRANSFORMER,
            query=transformer_code,
            asset=asset,
        )

    def search_by_feeder(self, feeder_code: str) -> list[OperationalSearchResult]:
        self.repository.initialize()
        assets = self.repository.get_assets_by_feeder(feeder_code)

        return [
            OperationalSearchResult(
                search_type=OperationalSearchType.FEEDER,
                query=feeder_code,
                asset=asset,
            )
            for asset in assets
        ]

    def search_by_substation(
        self,
        substation_code: str,
    ) -> list[OperationalSearchResult]:
        self.repository.initialize()
        assets = self.repository.get_assets_by_substation(substation_code)

        return [
            OperationalSearchResult(
                search_type=OperationalSearchType.SUBSTATION,
                query=substation_code,
                asset=asset,
            )
            for asset in assets
        ]

    def search_by_coordinates(
        self,
        latitude: float,
        longitude: float,
    ) -> OperationalSearchResult:
        self.repository.initialize()
        nearest = self.repository.find_nearest_asset(
            latitude=latitude,
            longitude=longitude,
        )

        if nearest is None:
            return OperationalSearchResult(
                search_type=OperationalSearchType.COORDINATES,
                query=f"{latitude},{longitude}",
                asset=None,
            )

        asset, distance_meters = nearest

        return OperationalSearchResult(
            search_type=OperationalSearchType.COORDINATES,
            query=f"{latitude},{longitude}",
            asset=asset,
            distance_meters=distance_meters,
        )
