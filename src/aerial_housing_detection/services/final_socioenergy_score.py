from src.aerial_housing_detection.domain.final_score import FinalSocioEnergyScore
from src.aerial_housing_detection.services.grid_aggregation import GridAggregationService
from src.aerial_housing_detection.services.socioenergy_analysis import (
    SocioEnergyAnalysisService,
)


class FinalSocioEnergyScoreService:
    def __init__(
        self,
        socioenergy_service: SocioEnergyAnalysisService | None = None,
        grid_aggregation_service: GridAggregationService | None = None,
    ) -> None:
        self.socioenergy_service = socioenergy_service or SocioEnergyAnalysisService()
        self.grid_aggregation_service = (
            grid_aggregation_service or GridAggregationService()
        )

    def build_scores(
        self,
        reference_month: str,
        estimated_roofs_by_area: dict[str, int],
    ) -> list[FinalSocioEnergyScore]:
        socioenergy_indicators = self.socioenergy_service.build_indicators(
            reference_month=reference_month,
            estimated_roofs_by_area=estimated_roofs_by_area,
        )
        transformer_summaries = (
            self.grid_aggregation_service.build_transformer_summaries(
                reference_month=reference_month,
            )
        )

        transformer_by_area = {
            summary.area_id: summary for summary in transformer_summaries
        }

        scores = []
        for indicator in socioenergy_indicators:
            transformer_summary = transformer_by_area.get(indicator.area_id)

            if transformer_summary is None:
                continue

            final_priority_score = self._calculate_final_priority_score(
                socioenergy_priority_score=indicator.socioenergy_priority_score,
                operational_priority_score=indicator.operational_priority_score,
                adjusted_loss_kwh=transformer_summary.adjusted_loss_kwh,
                solar_offset_ratio=transformer_summary.solar_offset_ratio,
                vulnerability_ratio=indicator.vulnerability_ratio,
            )

            scores.append(
                FinalSocioEnergyScore(
                    area_id=indicator.area_id,
                    reference_month=reference_month,
                    transformer_code=transformer_summary.transformer_code,
                    feeder=transformer_summary.feeder,
                    sector_id=indicator.sector_id,
                    territory_id=indicator.territory_id,
                    estimated_loss_kwh=transformer_summary.estimated_loss_kwh,
                    estimated_generation_kwh=(
                        transformer_summary.estimated_generation_kwh
                    ),
                    adjusted_loss_kwh=transformer_summary.adjusted_loss_kwh,
                    solar_offset_ratio=transformer_summary.solar_offset_ratio,
                    roof_customer_gap=indicator.roof_customer_gap,
                    household_customer_gap=indicator.household_customer_gap,
                    vulnerability_ratio=indicator.vulnerability_ratio,
                    operational_priority_score=indicator.operational_priority_score,
                    socioenergy_priority_score=indicator.socioenergy_priority_score,
                    final_priority_score=final_priority_score,
                    final_risk_level=self._risk_level(final_priority_score),
                )
            )

        return sorted(
            scores,
            key=lambda item: item.final_priority_score,
            reverse=True,
        )

    def _calculate_final_priority_score(
        self,
        socioenergy_priority_score: float,
        operational_priority_score: float,
        adjusted_loss_kwh: float,
        solar_offset_ratio: float,
        vulnerability_ratio: float,
    ) -> float:
        socioenergy_component = min(40.0, max(0.0, socioenergy_priority_score) * 0.4)
        operational_component = min(
            25.0,
            max(0.0, operational_priority_score) * 0.25,
        )
        adjusted_loss_component = min(20.0, max(0.0, adjusted_loss_kwh) / 250.0)
        vulnerability_component = min(15.0, max(0.0, vulnerability_ratio) * 15.0)
        solar_relief_component = min(20.0, max(0.0, solar_offset_ratio) * 20.0)

        score = (
            socioenergy_component
            + operational_component
            + adjusted_loss_component
            + vulnerability_component
            - solar_relief_component
        )

        return round(min(100.0, max(0.0, score)), 4)

    def _risk_level(self, score: float) -> str:
        if score >= 75.0:
            return "critical"
        if score >= 55.0:
            return "high"
        if score >= 35.0:
            return "medium"
        return "low"
