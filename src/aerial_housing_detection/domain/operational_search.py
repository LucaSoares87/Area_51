from dataclasses import dataclass
from enum import StrEnum


class OperationalSearchType(StrEnum):
    CUSTOMER = "customer"
    TRANSFORMER = "transformer"
    FEEDER = "feeder"
    SUBSTATION = "substation"
    COORDINATES = "coordinates"


@dataclass(frozen=True)
class OperationalAsset:
    area_id: str
    transformer_code: str
    feeder_code: str
    substation_code: str
    latitude: float
    longitude: float
    city: str
    neighborhood: str
    installed_power_kva: float | None = None
    operational_status: str | None = None


@dataclass(frozen=True)
class CustomerOperationalLink:
    customer_id: str
    area_id: str
    transformer_code: str
    feeder_code: str
    substation_code: str
    reference_month: str
    customer_status: str | None = None
    consumer_class: str | None = None


@dataclass(frozen=True)
class OperationalSearchResult:
    search_type: OperationalSearchType
    query: str
    asset: OperationalAsset | None
    customer_link: CustomerOperationalLink | None = None
    distance_meters: float | None = None
