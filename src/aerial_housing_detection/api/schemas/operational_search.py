from pydantic import BaseModel


class OperationalAssetResponse(BaseModel):
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


class CustomerOperationalLinkResponse(BaseModel):
    customer_id: str
    area_id: str
    transformer_code: str
    feeder_code: str
    substation_code: str
    reference_month: str
    customer_status: str | None = None
    consumer_class: str | None = None


class OperationalSearchResponse(BaseModel):
    search_type: str
    query: str
    asset: OperationalAssetResponse | None = None
    customer_link: CustomerOperationalLinkResponse | None = None
    distance_meters: float | None = None


class OperationalSearchListResponse(BaseModel):
    search_type: str
    query: str
    total_records: int
    records: list[OperationalSearchResponse]
