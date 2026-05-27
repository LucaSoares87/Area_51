from src.aerial_housing_detection.domain.territory_enrichment import (
    CrasContext,
    TerritoryContext,
)


class InMemoryCrasProvider:
    def __init__(self, default_context: CrasContext | None = None) -> None:
        self.default_context = default_context

    def get_context(self, context: TerritoryContext) -> CrasContext | None:
        has_coordinates = context.latitude is not None and context.longitude is not None

        if not has_coordinates and not context.postal_code:
            return None

        return self.default_context
