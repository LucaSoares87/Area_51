from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ConcessionariaAsset:
    transformer_code: str
    feeder_code: str
    substation_code: str
    latitude: float | None
    longitude: float | None
    city: str | None
    neighborhood: str | None
    postal_code: str | None
    customer_count: int
    transformer_input_kwh: float
    billed_consumption_kwh: float
    gd_injected_kwh: float
    technical_loss_kwh: float = 0.0


class ConcessionariaProvider(Protocol):
    def get_by_transformer(self, transformer_code: str) -> ConcessionariaAsset | None:
        pass

    def get_by_feeder(self, feeder_code: str) -> list[ConcessionariaAsset]:
        pass

    def get_by_substation(self, substation_code: str) -> list[ConcessionariaAsset]:
        pass

    def get_nearest_by_coordinates(
        self,
        latitude: float,
        longitude: float,
    ) -> ConcessionariaAsset | None:
        pass
