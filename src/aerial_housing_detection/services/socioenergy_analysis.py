from src.aerial_housing_detection.domain.socioenergy import SocioEnergyIndicator
from src.aerial_housing_detection.storage.loss_repository import LossRepository
from src.aerial_housing_detection.storage.territory_repository import (
    TerritoryRepository,
)


class SocioEnergyAnalysisService:
    def __init__(
        self,
        loss_repository: LossRepository | None = None,
        territory_repository: TerritoryRepository | None = None,
    ) -> None:
        self.loss_repository = loss_repository or LossRepository()
        self.territory_repository = territory_repository or TerritoryRepository()

    def build_indicators(
        self,
        reference_month: str,
        estimated_roofs_by_area: dict[str, int],
    ) -> list[SocioEnergyIndicator]:
        self.loss_repository.initialize()
        self.territory_repository.initialize()

        loss_records = self.loss_repository.list_monthly_loss_records(
            reference_month=reference_month,
        )

        indicators = []
        for loss_record in loss_records:
            area_id = str(loss_record["area_id"])
            estimated_roofs = estimated_roofs_by_area.get(area_id, 0)
            customer_count = int(loss_record["customer_count"])

            territorial_indicator = self.territory_repository.build_territorial_indicator(
                area_id=area_id,
                estimated_roofs=estimated_roofs,
                customer_count=customer_count,
            )

            if territorial_indicator is None:
                continue

            indicator = SocioEnergyIndicator(
                area_id=area_id,
                reference_month=reference_month,
                sector_id=territorial_indicator.sector_id,
                territory_id=territorial_indicator.territory_id,
                population=territorial_indicator.population,
                households=territorial_indicator.households,
                estimated_roofs=territorial_indicator.estimated_roofs,
                customer_count=territorial_indicator.customer_count,
                roof_customer_gap=territorial_indicator.roof_customer_gap,
                household_customer_gap=territorial_indicator.household_customer_gap,
                assisted_families=territorial_indicator.assisted_families,
                vulnerable_families=territorial_indicator.vulnerable_families,
                vulnerability_ratio=territorial_indicator.vulnerability_ratio,
                estimated_loss_kwh=float(loss_record["estimated_loss_kwh"]),
                estimated_loss_percent=float(loss_record["estimated_loss_percent"]),
                operational_risk_level=str(loss_record["risk_level"]),
                operational_priority_score=float(loss_record["priority_score"]),
                socioenergy_priority_score=self._calculate_socioenergy_score(
                    roof_customer_gap=territorial_indicator.roof_customer_gap,
                    household_customer_gap=territorial_indicator.household_customer_gap,
                    vulnerability_ratio=territorial_indicator.vulnerability_ratio,
                    estimated_loss_percent=float(loss_record["estimated_loss_percent"]),
                    operational_priority_score=float(loss_record["priority_score"]),
                ),
            )
            indicators.append(indicator)

        return sorted(
            indicators,
            key=lambda item: item.socioenergy_priority_score,
            reverse=True,
        )

    def _calculate_socioenergy_score(
        self,
        roof_customer_gap: int,
        household_customer_gap: int,
        vulnerability_ratio: float,
        estimated_loss_percent: float,
        operational_priority_score: float,
    ) -> float:
        roof_gap_component = min(20.0, max(0, roof_customer_gap) * 0.5)
        household_gap_component = min(20.0, max(0, household_customer_gap) * 0.5)
        vulnerability_component = min(25.0, max(0.0, vulnerability_ratio) * 25.0)
        loss_component = min(20.0, max(0.0, estimated_loss_percent) * 50.0)
        operational_component = min(15.0, max(0.0, operational_priority_score) * 0.15)

        score = (
            roof_gap_component
            + household_gap_component
            + vulnerability_component
            + loss_component
            + operational_component
        )

        return round(min(100.0, max(0.0, score)), 4)
