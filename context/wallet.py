from context.base import DefaultContext
from gettext import gettext as _

from database.check import get_checks_by_user
from settings.common import CRYPTO_SETTINGS
from units.btc import BTCUnit


class WalletContext(DefaultContext):
    async def ctx(self):
        btc_unit = BTCUnit(network=CRYPTO_SETTINGS['BTC']['network'])
        balance = await btc_unit.get_balance(address=self.user['profile']['address']['BTC'])
        return {
            'btc_balance': balance,
            'wallet_currency': self.user['profile']['wallet_currency'],
            'total_balance': 1000,
        }


class ReplenishContext(DefaultContext):
    async def ctx(self):
        return {}


class WithdrawContext(DefaultContext):
    async def ctx(self):
        return {}


class CryptoContext(DefaultContext):

    async def markup(self):
        selected = await self.selected()
        return [
            [
                [_('Назад'), selected[-2]],
            ],
        ]

    async def ctx(self):
        selected = await self.selected()
        crypto = selected[-1]
        action_type = selected[-2]
        ctx = {'crypto': crypto}
        address = self.user['profile']['address'][crypto]
        templates_map = {
            self.triggers.REPLENISH: ["wallet/replenish.html", {**ctx, 'address': address}],
            self.triggers.WITHDRAW: ["wallet/withdraw.html", ctx],
            self.triggers.CREATE_CHECK: [
                "wallet/check_amount.html",
                {
                    **ctx,
                    "max_value_fiat": 1000,  # TODO: берем из настроек
                    "min_value_fiat": 100,
                    "wallet_currency": self.user['profile']['wallet_currency'],
                    "min_check_amount": 0.001,
                    "max_check_amount": 2,
                },
            ],
            self.triggers.CREATE_BILL: [
                "wallet/bill_amount.html",
                {
                    **ctx,
                    "max_value_fiat": 1000,  # TODO: берем из настроек
                    "min_value_fiat": 100,
                    "wallet_currency": self.user['profile']['wallet_currency'],
                    "min_bill_amount": 0.001,
                    "max_bill_amount": 2,
                },
            ],
            self.triggers.USER_INPUT: ["user_input.html", {}],
        }
        template_data = templates_map.get(action_type, ["errors/error.html", {}])
        text = await self.render_template(template_data[0], template_data[1])
        return {'text': text}


class CheckContext(DefaultContext):
    async def markup(self):
        selected = await self.selected()

        user_checks = await get_checks_by_user(user_id=self.user['user_id'])

        # Создать кнопки для каждого чека
        check_buttons = [
            [[f"#{check['code']} на {check['amount']} {check['cryptocurrency']}", check['code']]]
            for check in user_checks
        ]
        check_buttons = await self.pagination(check_buttons, trigger=self.triggers.CHECK)

        keyboard = [
            *check_buttons,
            [[_('Создать чек'), self.triggers.CREATE_CHECK]],
            [[_('Назад'), selected[-2]]],
        ]

        return keyboard


class BillContext(DefaultContext):
    async def markup(self):
        selected = await self.selected()

        user_bills = await get_checks_by_user(user_id=self.user['user_id'])

        # Создать кнопки для каждого счета
        bill_buttons = [
            [[f"#{bill['code']} на {bill['amount']} {bill['cryptocurrency']}", bill['code']]] for bill in user_bills
        ]
        bill_buttons = await self.pagination(bill_buttons, trigger=self.triggers.BILL)

        keyboard = [
            *bill_buttons,
            [[_('Создать счет'), self.triggers.CREATE_BILL]],
            [[_('Назад'), selected[-2]]],
        ]

        return keyboard
