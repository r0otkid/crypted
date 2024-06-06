from decimal import Decimal
from typing import Tuple

from database.bill import get_bill_by_code
from database.check import get_check_by_code
from triggers import Triggers


class BaseMixin:
    pass


class UserInputMixin(BaseMixin):
    @staticmethod
    async def get_model_amount_in_fiat(rates: dict, code: str, trigger: str) -> Tuple[dict, Decimal]:
        function = get_check_by_code if trigger == Triggers.CHECK else get_bill_by_code
        instance = await function(code)
        return instance, round(
            Decimal(str(instance['amount'])) * Decimal(str(rates.get(instance['cryptocurrency'], 0))), 2
        )
