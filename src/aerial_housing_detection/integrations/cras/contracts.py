from typing import Protocol

from src.aerial_housing_detection.domain.territory_enrichment import (
    CrasContext,
    TerritoryContext,
)


class CrasProvider(Protocol):
    def get_context(self, context: TerritoryContext) -> CrasContext | None:
        pass
