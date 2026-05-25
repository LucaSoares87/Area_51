from src.aerial_housing_detection.domain.solar import SolarAdjustedLoss
from src.aerial_housing_detection.storage.loss_repository import LossRepository
from src.aerial_housing_detection.storage.solar_repository import SolarRepository


class SolarBalanceService:
    def __init__(
        self,
        loss_repository: LossRepository | None = None,
        solar_repository: SolarRepository | None = None,
    ) -> None:
        self.loss_repository = loss_repository or LossRepository()
        self.solar_repository = solar_repository or SolarRepository()

    def build_adjusted_losses(
        self,
        reference_month: str,
    ) -> list[SolarAdjustedLoss]:
        self.loss_repository.initialize()
        self.solar_repository.initialize()

        loss_records = self.loss_repository.list_monthly_loss_records(
            reference_month=reference_month,
        )

        adjusted_losses = []
        for loss_record in loss_records:
            area_id = str(loss_record["area_id"])
            estimated_loss_kwh = float(loss_record["estimated_loss_kwh"])
            solar_estimate = self.solar_repository.get_estimate(
                area_id=area_id,
                reference_month=reference_month,
            )
            estimated_generation_kwh = 0.0

            if solar_estimate is not None:
                estimated_generation_kwh = float(
                    solar_estimate["estimated_generation_kwh"],
                )

            adjusted_loss_kwh = max(
                0.0,
                estimated_loss_kwh - estimated_generation_kwh,
            )
            solar_offset_ratio = self._calculate_solar_offset_ratio(
                estimated_loss_kwh=estimated_loss_kwh,
                estimated_generation_kwh=estimated_generation_kwh,
            )

            adjusted_losses.append(
                SolarAdjustedLoss(
                    area_id=area_id,
                    reference_month=reference_month,
                    estimated_loss_kwh=round(estimated_loss_kwh, 4),
                    estimated_generation_kwh=round(estimated_generation_kwh, 4),
                    adjusted_loss_kwh=round(adjusted_loss_kwh, 4),
                    solar_offset_ratio=solar_offset_ratio,
                )
            )

        return sorted(
            adjusted_losses,
            key=lambda item: item.adjusted_loss_kwh,
            reverse=True,
        )

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
