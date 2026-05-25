from src.aerial_housing_detection.domain.solar import SolarAreaEstimate
from src.aerial_housing_detection.integrations.gd.contracts import GDMonthlyBalance


class GDToSolarEstimateNormalizer:
    def normalize(self, balances: list[GDMonthlyBalance]) -> list[SolarAreaEstimate]:
        estimates = []

        for balance in balances:
            if not balance.area_id:
                continue

            estimates.append(
                SolarAreaEstimate(
                    area_id=balance.area_id,
                    reference_month=balance.reference_month,
                    solar_panel_count=balance.gd_customer_count,
                    estimated_solar_area_m2=self._estimate_area_from_capacity(
                        balance.installed_capacity_kwp,
                    ),
                    estimated_generation_kwh=balance.injected_to_grid_kwh,
                    confidence_score=balance.confidence_score,
                )
            )

        return estimates

    def _estimate_area_from_capacity(self, installed_capacity_kwp: float) -> float:
        return round(max(0.0, installed_capacity_kwp) * 6.0, 4)
