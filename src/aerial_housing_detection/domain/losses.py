from dataclasses import dataclass
from enum import StrEnum


class LossRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class OperationalArea:
    area_id: str
    transformer_code: str
    latitude: float
    longitude: float
    neighborhood: str
    city: str
    feeder: str
    customer_count: int


@dataclass(frozen=True)
class MonthlyLossRecord:
    area_id: str
    reference_month: str
    injected_energy_kwh: float
    billed_consumption_kwh: float
    estimated_loss_kwh: float
    estimated_loss_percent: float
    risk_level: LossRiskLevel
    priority_score: float


class LossCalculator:
    def calculate_record(
        self,
        area_id: str,
        reference_month: str,
        injected_energy_kwh: float,
        billed_consumption_kwh: float,
    ) -> MonthlyLossRecord:
        if injected_energy_kwh <= 0:
            estimated_loss_kwh = 0.0
            estimated_loss_percent = 0.0
        else:
            estimated_loss_kwh = max(0.0, injected_energy_kwh - billed_consumption_kwh)
            estimated_loss_percent = estimated_loss_kwh / injected_energy_kwh

        risk_level = self.classify_risk(estimated_loss_percent)
        priority_score = self.calculate_priority_score(
            estimated_loss_kwh=estimated_loss_kwh,
            estimated_loss_percent=estimated_loss_percent,
        )

        return MonthlyLossRecord(
            area_id=area_id,
            reference_month=reference_month,
            injected_energy_kwh=round(injected_energy_kwh, 4),
            billed_consumption_kwh=round(billed_consumption_kwh, 4),
            estimated_loss_kwh=round(estimated_loss_kwh, 4),
            estimated_loss_percent=round(estimated_loss_percent, 6),
            risk_level=risk_level,
            priority_score=priority_score,
        )

    def classify_risk(self, estimated_loss_percent: float) -> LossRiskLevel:
        if estimated_loss_percent >= 0.35:
            return LossRiskLevel.CRITICAL

        if estimated_loss_percent >= 0.2:
            return LossRiskLevel.HIGH

        if estimated_loss_percent >= 0.1:
            return LossRiskLevel.MEDIUM

        return LossRiskLevel.LOW

    def calculate_priority_score(
        self,
        estimated_loss_kwh: float,
        estimated_loss_percent: float,
    ) -> float:
        loss_volume_component = min(60.0, estimated_loss_kwh / 100.0)
        loss_percent_component = min(40.0, estimated_loss_percent * 100.0)
        return round(loss_volume_component + loss_percent_component, 4)
