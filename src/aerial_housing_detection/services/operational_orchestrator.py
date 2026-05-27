from dataclasses import dataclass

from src.aerial_housing_detection.domain.territory_enrichment import (
    TerritoryContext,
    TerritoryEnrichmentResult,
    choose_territory_lookup_strategy,
)
from src.aerial_housing_detection.integrations.concessionaria.contracts import (
    ConcessionariaAsset,
    ConcessionariaProvider,
)
from src.aerial_housing_detection.integrations.cras.contracts import CrasProvider
from src.aerial_housing_detection.integrations.ibge.contracts import IbgeProvider
from src.aerial_housing_detection.services.loss_inference import (
    LossInferenceInput,
    LossInferenceResult,
    LossInferenceService,
)


@dataclass(frozen=True)
class OperationalAnalysisResult:
    query_type: str
    query: str
    asset: ConcessionariaAsset | None
    inference: LossInferenceResult | None
    territory: TerritoryEnrichmentResult | None


class OperationalOrchestrator:
    def __init__(
        self,
        concessionaria_provider: ConcessionariaProvider,
        ibge_provider: IbgeProvider,
        cras_provider: CrasProvider,
        loss_inference_service: LossInferenceService | None = None,
    ) -> None:
        self.concessionaria_provider = concessionaria_provider
        self.ibge_provider = ibge_provider
        self.cras_provider = cras_provider
        self.loss_inference_service = loss_inference_service or LossInferenceService()

    def analyze_transformer(self, transformer_code: str) -> OperationalAnalysisResult:
        asset = self.concessionaria_provider.get_by_transformer(transformer_code)
        return self._build_result("transformer", transformer_code, asset)

    def analyze_coordinates(
        self,
        latitude: float,
        longitude: float,
    ) -> OperationalAnalysisResult:
        asset = self.concessionaria_provider.get_nearest_by_coordinates(
            latitude,
            longitude,
        )
        query = f"{latitude},{longitude}"

        return self._build_result("coordinates", query, asset)

    def _build_result(
        self,
        query_type: str,
        query: str,
        asset: ConcessionariaAsset | None,
    ) -> OperationalAnalysisResult:
        if asset is None:
            return OperationalAnalysisResult(
                query_type=query_type,
                query=query,
                asset=None,
                inference=None,
                territory=None,
            )

        territory_context = TerritoryContext(
            latitude=asset.latitude,
            longitude=asset.longitude,
            postal_code=asset.postal_code,
            city=asset.city,
            neighborhood=asset.neighborhood,
        )

        inference = self.loss_inference_service.infer(
            LossInferenceInput(
                transformer_input_kwh=asset.transformer_input_kwh,
                billed_consumption_kwh=asset.billed_consumption_kwh,
                gd_injected_kwh=asset.gd_injected_kwh,
                technical_loss_kwh=asset.technical_loss_kwh,
                estimated_houses=asset.customer_count,
            )
        )

        territory = TerritoryEnrichmentResult(
            ibge=self.ibge_provider.get_context(territory_context),
            cras=self.cras_provider.get_context(territory_context),
            source_strategy=choose_territory_lookup_strategy(territory_context),
        )

        return OperationalAnalysisResult(
            query_type=query_type,
            query=query,
            asset=asset,
            inference=inference,
            territory=territory,
        )
