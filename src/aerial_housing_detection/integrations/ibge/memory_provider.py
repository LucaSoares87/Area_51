from src.aerial_housing_detection.domain.territory_enrichment import (
    IbgeContext,
    TerritoryContext,
)


class InMemoryIbgeProvider:
    def __init__(self, default_context: IbgeContext | None = None) -> None:
        self.default_context = default_context

    def get_context(self, context: TerritoryContext) -> IbgeContext | None:
        has_coordinates = context.latitude is not None and context.longitude is not None

        if not has_coordinates and not context.postal_code:
            return None

        return self.default_context
