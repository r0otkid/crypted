from settings.common import BOT_NAME
from decimal import Decimal, InvalidOperation
from context.validators.base import DefaultValidator
from database.bill import create_bill
from database.check import create_check


class CheckAmountValidator(DefaultValidator):
    async def validate(self, value: str) -> str:
        selected = await self.context.selected()
        bot_settings = await self.context.bot_settings
        rates = await self.context.get_rates()
        rate = rates.get(selected[-2], 0)

        await self.clear_chain(selected)

        min_check_amount = bot_settings['limits'][selected[-2]]['min']
        max_check_amount = bot_settings['limits'][selected[-2]]['max']

        text = await self.context.render_template('errors/create_check_error.html', {
            "crypto": selected[-2],
            "balance": self.context.user['profile']['wallet'][selected[-2]]['balance'],
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
                    "fiat_amount": round(check.amount * rate, 2),
                    "check": check,
                    "wallet_currency": self.user['profile']['wallet_currency'],
                    "bot_name": BOT_NAME
                })
        except InvalidOperation:
            pass
        return text

class BillAmountValidator(DefaultValidator):
    async def validate(self, value: str) -> str:
        selected = await self.context.selected()
        bot_settings = await self.context.bot_settings
        rates = await self.context.get_rates()
        rate = rates.get(selected[-2], 0)

        await self.clear_chain(selected)

        min_bill_amount = bot_settings['limits'][selected[-2]]['min']
        max_bill_amount = bot_settings['limits'][selected[-2]]['max']
        
        text = await self.context.render_template('errors/create_bill_error.html', {
            "crypto": selected[-2],
            "balance": self.context.user['profile']['wallet'][selected[-2]]['balance'],
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
                    "fiat_amount": round(bill.amount * rate, 2),
                    "bill": bill,
                    "wallet_currency": self.user['profile']['wallet_currency'],
                    "bot_name": BOT_NAME
                })
        except InvalidOperation:
            pass
        return text