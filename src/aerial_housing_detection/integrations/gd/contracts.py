from dataclasses import dataclass
from enum import StrEnum


class GDSourceType(StrEnum):
    API = "api"
    CSV = "csv"
    EXCEL = "excel"
    DATABASE = "database"
    MANUAL = "manual"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class GDQuery:
    reference_month: str
    area_id: str | None = None
    transformer_code: str | None = None
    feeder_code: str | None = None
    substation_code: str | None = None


@dataclass(frozen=True)
class GDMonthlyBalance:
    reference_month: str
    area_id: str | None
    transformer_code: str | None
    feeder_code: str | None
    substation_code: str | None
    gd_customer_count: int
    installed_capacity_kwp: float
    generated_energy_kwh: float
    consumed_energy_kwh: float
    injected_to_grid_kwh: float
    received_from_grid_kwh: float
    compensated_energy_kwh: float
    source_type: GDSourceType
    confidence_score: float

    @property
    def net_injected_energy_kwh(self) -> float:
        return max(0.0, self.injected_to_grid_kwh - self.received_from_grid_kwh)

    @property
    def self_consumption_kwh(self) -> float:
        return max(0.0, self.generated_energy_kwh - self.injected_to_grid_kwh)

    @property
    def has_relevant_grid_injection(self) -> bool:
        return self.injected_to_grid_kwh > 0
