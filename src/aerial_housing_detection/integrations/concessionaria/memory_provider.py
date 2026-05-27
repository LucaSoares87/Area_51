from math import atan2, cos, radians, sin, sqrt

from src.aerial_housing_detection.integrations.concessionaria.contracts import (
    ConcessionariaAsset,
    ConcessionariaProvider,
)


class InMemoryConcessionariaProvider(ConcessionariaProvider):
    def __init__(self, assets: list[ConcessionariaAsset]) -> None:
        self.assets = assets

    def get_by_transformer(self, transformer_code: str) -> ConcessionariaAsset | None:
        normalized = transformer_code.strip().upper()

        return next(
            (
                asset
                for asset in self.assets
                if asset.transformer_code.upper() == normalized
            ),
            None,
        )

    def get_by_feeder(self, feeder_code: str) -> list[ConcessionariaAsset]:
        normalized = feeder_code.strip().upper()

        return [
            asset
            for asset in self.assets
            if asset.feeder_code.upper() == normalized
        ]

    def get_by_substation(self, substation_code: str) -> list[ConcessionariaAsset]:
        normalized = substation_code.strip().upper()

        return [
            asset
            for asset in self.assets
            if asset.substation_code.upper() == normalized
        ]

    def get_nearest_by_coordinates(
        self,
        latitude: float,
        longitude: float,
    ) -> ConcessionariaAsset | None:
        candidates = [
            asset
            for asset in self.assets
            if asset.latitude is not None and asset.longitude is not None
        ]

        if not candidates:
            return None

        return min(
            candidates,
            key=lambda asset: _distance_km(
                latitude,
                longitude,
                float(asset.latitude),
                float(asset.longitude),
            ),
        )


def _distance_km(
    origin_latitude: float,
    origin_longitude: float,
    target_latitude: float,
    target_longitude: float,
) -> float:
    radius_km = 6371.0

    delta_latitude = radians(target_latitude - origin_latitude)
    delta_longitude = radians(target_longitude - origin_longitude)

    lat1 = radians(origin_latitude)
    lat2 = radians(target_latitude)

    value = (
        sin(delta_latitude / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_longitude / 2) ** 2
    )

    return radius_km * 2 * atan2(sqrt(value), sqrt(1 - value))
