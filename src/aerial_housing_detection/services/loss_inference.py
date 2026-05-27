from dataclasses import dataclass

from src.aerial_housing_detection.domain.energy_balance import (
    EnergyBalanceInput,
    EnergyBalanceResult,
    calculate_energy_balance,
)


@dataclass(frozen=True)
class LossInferenceInput:
    transformer_input_kwh: float
    billed_consumption_kwh: float
    gd_injected_kwh: float
    technical_loss_kwh: float = 0.0
    estimated_houses: int | None = None


@dataclass(frozen=True)
class LossInferenceResult:
    energy_balance: EnergyBalanceResult
    priority: str
    score: int
    explanation: list[str]


class LossInferenceService:
    def infer(self, payload: LossInferenceInput) -> LossInferenceResult:
        balance = calculate_energy_balance(
            EnergyBalanceInput(
                transformer_input_kwh=payload.transformer_input_kwh,
                billed_consumption_kwh=payload.billed_consumption_kwh,
                gd_injected_kwh=payload.gd_injected_kwh,
                technical_loss_kwh=payload.technical_loss_kwh,
                estimated_houses=payload.estimated_houses,
            )
        )

        score = self._score(balance)
        priority = self._priority(score)

        return LossInferenceResult(
            energy_balance=balance,
            priority=priority,
            score=score,
            explanation=self._explain(balance, priority),
        )

    def _score(self, balance: EnergyBalanceResult) -> int:
        score = 0

        if balance.estimated_loss_percent >= 20:
            score += 45
        elif balance.estimated_loss_percent >= 12:
            score += 30
        elif balance.estimated_loss_percent >= 6:
            score += 15

        if balance.estimated_loss_kwh >= 25000:
            score += 30
        elif balance.estimated_loss_kwh >= 10000:
            score += 20
        elif balance.estimated_loss_kwh >= 5000:
            score += 10

        if self._has_relevant_loss_per_house(balance):
            score += 20

        return min(score, 100)

    def _priority(self, score: int) -> str:
        if score >= 70:
            return "Alta"

        if score >= 40:
            return "Média"

        return "Baixa"

    def _explain(
        self,
        balance: EnergyBalanceResult,
        priority: str,
    ) -> list[str]:
        explanation = [
            f"Prioridade operacional {priority.lower()} calculada pelo balanço energético.",
            f"Perda estimada de {balance.estimated_loss_kwh:.2f} kWh.",
            f"Percentual estimado de perda de {balance.estimated_loss_percent:.2f}%.",
        ]

        if balance.gd_injected_kwh > 0:
            explanation.append(
                f"GD considerada no ajuste: {balance.gd_injected_kwh:.2f} kWh."
            )

        if balance.estimated_loss_per_house_kwh is not None:
            explanation.append(
                "Perda estimada por casa de "
                f"{balance.estimated_loss_per_house_kwh:.2f} kWh."
            )

        return explanation

    def _has_relevant_loss_per_house(self, balance: EnergyBalanceResult) -> bool:
        return (
            balance.estimated_loss_per_house_kwh is not None
            and balance.estimated_loss_per_house_kwh >= 250
        )
