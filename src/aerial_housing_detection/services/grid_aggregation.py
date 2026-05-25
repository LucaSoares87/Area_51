from collections import defaultdict

from src.aerial_housing_detection.domain.grid_aggregation import (
    FeederLossSummary,
    TransformerLossSummary,
)
from src.aerial_housing_detection.storage.loss_repository import LossRepository
from src.aerial_housing_detection.storage.solar_repository import SolarRepository


class GridAggregationService:
    def __init__(
        self,
        loss_repository: LossRepository | None = None,
        solar_repository: SolarRepository | None = None,
    ) -> None:
        self.loss_repository = loss_repository or LossRepository()
        self.solar_repository = solar_repository or SolarRepository()

    def build_transformer_summaries(
        self,
        reference_month: str,
    ) -> list[TransformerLossSummary]:
        self.loss_repository.initialize()
        self.solar_repository.initialize()

        records = self.loss_repository.list_monthly_loss_records(
            reference_month=reference_month,
        )

        summaries = []
        for record in records:
            area_id = str(record["area_id"])
            estimated_loss_kwh = float(record["estimated_loss_kwh"])
            estimated_generation_kwh = self._get_estimated_generation_kwh(
                area_id=area_id,
                reference_month=reference_month,
            )
            adjusted_loss_kwh = max(
                0.0,
                estimated_loss_kwh - estimated_generation_kwh,
            )
            solar_offset_ratio = self._calculate_solar_offset_ratio(
                estimated_loss_kwh=estimated_loss_kwh,
                estimated_generation_kwh=estimated_generation_kwh,
            )

            summaries.append(
                TransformerLossSummary(
                    area_id=area_id,
                    transformer_code=str(record["transformer_code"]),
                    feeder=str(record["feeder"]),
                    reference_month=reference_month,
                    customer_count=int(record["customer_count"]),
                    estimated_loss_kwh=round(estimated_loss_kwh, 4),
                    estimated_generation_kwh=round(estimated_generation_kwh, 4),
                    adjusted_loss_kwh=round(adjusted_loss_kwh, 4),
                    estimated_loss_percent=float(record["estimated_loss_percent"]),
                    solar_offset_ratio=solar_offset_ratio,
                    priority_score=float(record["priority_score"]),
                    risk_level=str(record["risk_level"]),
                )
            )

        return sorted(
            summaries,
            key=lambda item: item.adjusted_loss_kwh,
            reverse=True,
        )

    def build_feeder_summaries(
        self,
        reference_month: str,
    ) -> list[FeederLossSummary]:
        transformer_summaries = self.build_transformer_summaries(
            reference_month=reference_month,
        )
        grouped_summaries: dict[str, list[TransformerLossSummary]] = defaultdict(list)

        for summary in transformer_summaries:
            grouped_summaries[summary.feeder].append(summary)

        feeder_summaries = []
        for feeder, summaries in grouped_summaries.items():
            feeder_summaries.append(
                FeederLossSummary(
                    feeder=feeder,
                    reference_month=reference_month,
                    transformer_count=len(summaries),
                    customer_count=sum(item.customer_count for item in summaries),
                    estimated_loss_kwh=round(
                        sum(item.estimated_loss_kwh for item in summaries),
                        4,
                    ),
                    estimated_generation_kwh=round(
                        sum(item.estimated_generation_kwh for item in summaries),
                        4,
                    ),
                    adjusted_loss_kwh=round(
                        sum(item.adjusted_loss_kwh for item in summaries),
                        4,
                    ),
                    average_loss_percent=self._average(
                        [item.estimated_loss_percent for item in summaries],
                    ),
                    average_solar_offset_ratio=self._average(
                        [item.solar_offset_ratio for item in summaries],
                    ),
                    average_priority_score=self._average(
                        [item.priority_score for item in summaries],
                    ),
                    critical_transformers=sum(
                        1 for item in summaries if item.risk_level == "critical"
                    ),
                    high_risk_transformers=sum(
                        1 for item in summaries if item.risk_level == "high"
                    ),
                )
            )

        return sorted(
            feeder_summaries,
            key=lambda item: item.adjusted_loss_kwh,
            reverse=True,
        )

    def _get_estimated_generation_kwh(
        self,
        area_id: str,
        reference_month: str,
    ) -> float:
        estimate = self.solar_repository.get_estimate(
            area_id=area_id,
            reference_month=reference_month,
        )

        if estimate is None:
            return 0.0

        return float(estimate["estimated_generation_kwh"])

    def _calculate_solar_offset_ratio(
        self,
        estimated_loss_kwh: float,
        estimated_generation_kwh: float,
    ) -> float:
        if estimated_loss_kwh <= 0:
            return 0.0

        return round(
            min(1.0, max(0.0, estimated_generation_kwh / estimated_loss_kwh)),
            6,
        )

    def _average(self, values: list[float]) -> float:
        if not values:
            return 0.0

        return round(sum(values) / len(values), 6)
