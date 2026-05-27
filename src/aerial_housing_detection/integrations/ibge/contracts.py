from typing import Protocol

from src.aerial_housing_detection.domain.territory_enrichment import (
    IbgeContext,
    TerritoryContext,
)


class IbgeProvider(Protocol):
    def get_context(self, context: TerritoryContext) -> IbgeContext | None:
        pass
