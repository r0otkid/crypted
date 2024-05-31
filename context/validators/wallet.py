from decimal import Decimal, InvalidOperation
from context.validators.base import DefaultValidator
from database.bill import create_bill
from database.check import create_check


class CheckAmountValidator(DefaultValidator):
    async def validate(self, value: str) -> str:
        selected = await self.context.selected()

        await self.clear_chain(selected)

        min_check_amount = 0.001  # TODO: берем из настроек
        max_check_amount = 2

        text = await self.context.render_template('errors/create_check_error.html', {
            "crypto": selected[-2],
            "balance": Decimal('1.777'),  # TODO: берем из профиля
            "min_check_amount": min_check_amount,
            "max_check_amount": max_check_amount,
        })
        try:
            value = Decimal(value)
            if min_check_amount < value < max_check_amount:
                await self.update_chain(selected=selected, value=value)
                check = await create_check(
                    user=self.context.user,
                    amount=value,
                    cryptocurrency=selected[-2]
                )
                text = await self.context.render_template('wallet/check.html', {
                    "fiat_amount": 777,  #  TODO: посчитать по курсу
                    "check": check,
                    "wallet_currency": "RUB",  # TODO: берем из профиля
                    "bot_name": "Crawler_Robot"  #  TODO: берем из конфига
                })
        except InvalidOperation:
            pass
        return text

class BillAmountValidator(DefaultValidator):
    async def validate(self, value: str) -> str:
        selected = await self.context.selected()

        await self.clear_chain(selected)

        min_bill_amount = 0.001  # TODO: берем из настроек
        max_bill_amount = 2

        text = await self.context.render_template('errors/create_bill_error.html', {
            "crypto": selected[-2],
            "balance": Decimal('1.777'),  # TODO: берем из профиля
            "min_bill_amount": min_bill_amount,
            "max_bill_amount": max_bill_amount,
        })
        try:
            value = Decimal(value)
            if min_bill_amount < value < max_bill_amount:
                await self.update_chain(selected=selected, value=value)
                bill = await create_bill(
                    user=self.context.user,
                    amount=value,
                    cryptocurrency=selected[-2]
                )
                text = await self.context.render_template('wallet/bill.html', {
                    "fiat_amount": 777,  #  TODO: посчитать по курсу
                    "bill": bill,
                    "wallet_currency": "RUB",  # TODO: берем из профиля
                    "bot_name": "Crawler_Robot"  #  TODO: берем из конфига
                })
        except InvalidOperation:
            pass
        return text