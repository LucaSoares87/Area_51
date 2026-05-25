from dataclasses import dataclass


@dataclass(frozen=True)
class CensusSector:
    sector_id: str
    city: str
    state: str
    neighborhood: str
    population: int
    households: int
    average_residents_per_household: float


@dataclass(frozen=True)
class SocialAssistanceTerritory:
    territory_id: str
    cras_code: str
    cras_name: str
    city: str
    state: str
    neighborhood: str
    assisted_families: int
    vulnerable_families: int


@dataclass(frozen=True)
class OperationalTerritoryLink:
    area_id: str
    sector_id: str
    territory_id: str


@dataclass(frozen=True)
class TerritorialIndicator:
    area_id: str
    sector_id: str
    territory_id: str
    population: int
    households: int
    estimated_roofs: int
    customer_count: int
    assisted_families: int
    vulnerable_families: int
    roof_customer_gap: int
    household_customer_gap: int
    vulnerability_ratio: float
