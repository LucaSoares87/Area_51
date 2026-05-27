from dataclasses import dataclass


@dataclass(frozen=True)
class TerritoryContext:
    latitude: float | None
    longitude: float | None
    postal_code: str | None
    city: str | None
    neighborhood: str | None


@dataclass(frozen=True)
class IbgeContext:
    sector_id: str | None
    population: int | None
    households: int | None
    average_income: float | None
    vulnerability_index: float | None


@dataclass(frozen=True)
class CrasContext:
    territory_id: str | None
    cras_name: str | None
    vulnerability_level: str | None
    families_assisted: int | None
    vulnerability_index: float | None


@dataclass(frozen=True)
class TerritoryEnrichmentResult:
    ibge: IbgeContext | None
    cras: CrasContext | None
    source_strategy: str


def choose_territory_lookup_strategy(context: TerritoryContext) -> str:
    if context.latitude is not None and context.longitude is not None:
        return "coordinates"

    if context.postal_code:
        return "postal_code"

    if context.city and context.neighborhood:
        return "city_neighborhood"

    return "insufficient_data"
