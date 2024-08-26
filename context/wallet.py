import asyncio
from context.base import DefaultContext
from gettext import gettext as _
from database.bill import get_bills_by_user
from database.check import get_checks_by_user
from database.user import get_user_by_id, save_user
from settings.common import CRYPTO_SETTINGS, CRYPTOS
from utils import get_unit


class WalletContext(DefaultContext):
    async def ctx(self):
        db_user = await get_user_by_id(user_id=self.user['user_id'])

        balances = {crypto: db_user['profile']['wallet'][crypto]['balance'] for crypto in CRYPTOS}

        asyncio.create_task(self._update_wallet_balances())  # Запуск асинхронного обновления балансов

        rates = await self.get_rates()
        wallet_currency = self.user['profile']['wallet_currency']

        fiat_balances = {
            crypto: round(rates.get(crypto, 0) * balances[crypto] * rates.get(wallet_currency, 0), 2)
            for crypto in CRYPTOS
        }

        result = {f"{crypto.lower()}_balance": self.format(value=balances[crypto], crypto=crypto) for crypto in CRYPTOS}
        result.update({f"{crypto.lower()}_balance_fiat": fiat_balances[crypto] for crypto in CRYPTOS})
        result.update(
            {
                f"{crypto.lower()}_wallet_link": get_unit(crypto)(
                    network=CRYPTO_SETTINGS[crypto]['network']
                ).get_wallet_url(db_user['profile']['wallet'][crypto]['address'])
                for crypto in CRYPTOS
            }
        )
        result['wallet_currency'] = wallet_currency
        result['total_balance'] = round(sum(fiat_balances.values()), 2)

        return result

    async def _update_wallet_balances(self):
        db_user = await get_user_by_id(user_id=self.user['user_id'])

        for crypto in CRYPTOS:
            unit = get_unit(crypto)
            address = self.user['profile']['wallet'][crypto]['address']
            balance = await unit(network=CRYPTO_SETTINGS[crypto]['network']).get_balance(address=address)
            if balance:
                db_user['profile']['wallet'][crypto]['balance'] = balance

        await save_user(user_id=self.user['user_id'], user_data=db_user)


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
        address = self.user['profile']['wallet'][crypto]['address']
        bot_settings = await self.bot_settings
        min_amount = bot_settings['limits'][crypto]['min']
        max_amount = bot_settings['limits'][crypto]['max']
        rates = await self.get_rates()
        rate = rates.get(crypto, 0)
        templates_map = {
            self.triggers.REPLENISH: [
                "wallet/replenish.html",
                {**ctx, 'address': address, 'network': CRYPTO_SETTINGS[crypto]['network']},
            ],
            self.triggers.WITHDRAW: ["wallet/withdraw.html", ctx],
            self.triggers.CREATE_CHECK: [
                "wallet/check_amount.html",
                {
                    **ctx,
                    "max_value_fiat": round(max_amount * rate, 2),
                    "min_value_fiat": round(min_amount * rate, 2),
                    "wallet_currency": self.user['profile']['wallet_currency'],
                    "min_check_amount": min_amount,
                    "max_check_amount": max_amount,
                },
            ],
            self.triggers.CREATE_BILL: [
                "wallet/bill_amount.html",
                {
                    **ctx,
                    "max_value_fiat": round(max_amount * rate, 2),
                    "min_value_fiat": round(min_amount * rate, 2),
                    "wallet_currency": self.user['profile']['wallet_currency'],
                    "min_bill_amount": min_amount,
                    "max_bill_amount": max_amount,
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

        user_bills = await get_bills_by_user(user_id=self.user['user_id'])

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
