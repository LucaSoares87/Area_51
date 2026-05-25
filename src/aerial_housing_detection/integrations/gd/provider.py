from abc import ABC, abstractmethod

from src.aerial_housing_detection.integrations.gd.contracts import (
    GDMonthlyBalance,
    GDQuery,
)


class GDProvider(ABC):
    @abstractmethod
    def get_monthly_balance(self, query: GDQuery) -> list[GDMonthlyBalance]:
        """Return monthly GD balances for the given query."""
        pass
