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


@dataclass(frozen=True)
class OperationalRiskInput:
    estimated_loss_kwh: float
    estimated_loss_percent: float
    customer_count: int = 0
    recurrence_months: int = 1


class OperationalRiskScorer:
    """Calculates an operational priority score for field inspection."""

    def calculate_score(self, risk_input: OperationalRiskInput) -> float:
        loss_volume_component = self._loss_volume_component(
            risk_input.estimated_loss_kwh,
        )
        loss_percent_component = self._loss_percent_component(
            risk_input.estimated_loss_percent,
        )
        customer_component = self._customer_component(
            risk_input.customer_count,
        )
        recurrence_component = self._recurrence_component(
            risk_input.recurrence_months,
        )

        score = (
            loss_volume_component
            + loss_percent_component
            + customer_component
            + recurrence_component
        )

        return round(min(100.0, max(0.0, score)), 4)

    def _loss_volume_component(self, estimated_loss_kwh: float) -> float:
        return min(35.0, max(0.0, estimated_loss_kwh) / 200.0)

    def _loss_percent_component(self, estimated_loss_percent: float) -> float:
        return min(35.0, max(0.0, estimated_loss_percent) * 100.0)

    def _customer_component(self, customer_count: int) -> float:
        return min(15.0, max(0, customer_count) / 20.0)

    def _recurrence_component(self, recurrence_months: int) -> float:
        return min(15.0, max(0, recurrence_months) * 5.0)


class LossCalculator:
    def __init__(self, risk_scorer: OperationalRiskScorer | None = None) -> None:
        self.risk_scorer = risk_scorer or OperationalRiskScorer()

    def calculate_record(
        self,
        area_id: str,
        reference_month: str,
        injected_energy_kwh: float,
        billed_consumption_kwh: float,
        customer_count: int = 0,
        recurrence_months: int = 1,
    ) -> MonthlyLossRecord:
        if injected_energy_kwh <= 0:
            estimated_loss_kwh = 0.0
            estimated_loss_percent = 0.0
        else:
            estimated_loss_kwh = max(0.0, injected_energy_kwh - billed_consumption_kwh)
            estimated_loss_percent = estimated_loss_kwh / injected_energy_kwh

        risk_level = self.classify_risk(estimated_loss_percent)
        priority_score = self.risk_scorer.calculate_score(
            OperationalRiskInput(
                estimated_loss_kwh=estimated_loss_kwh,
                estimated_loss_percent=estimated_loss_percent,
                customer_count=customer_count,
                recurrence_months=recurrence_months,
            )
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
