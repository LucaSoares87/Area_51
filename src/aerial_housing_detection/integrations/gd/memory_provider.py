from src.aerial_housing_detection.integrations.gd.contracts import (
    GDMonthlyBalance,
    GDQuery,
)
from src.aerial_housing_detection.integrations.gd.provider import GDProvider


class InMemoryGDProvider(GDProvider):
    def __init__(self, balances: list[GDMonthlyBalance] | None = None) -> None:
        self.balances = balances or []

    def get_monthly_balance(self, query: GDQuery) -> list[GDMonthlyBalance]:
        return [
            balance
            for balance in self.balances
            if self._matches_query(balance=balance, query=query)
        ]

    def _matches_query(self, balance: GDMonthlyBalance, query: GDQuery) -> bool:
        if balance.reference_month != query.reference_month:
            return False

        if query.area_id and balance.area_id != query.area_id:
            return False

        if query.transformer_code and balance.transformer_code != query.transformer_code:
            return False

        if query.feeder_code and balance.feeder_code != query.feeder_code:
            return False

        return not (
            query.substation_code
            and balance.substation_code != query.substation_code
        )
