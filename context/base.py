from decimal import Decimal
from typing import Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from jinja2 import Environment, FileSystemLoader
from validators.wallet import BillAmountValidator, CheckAmountValidator, WithdrawAddressValidator, WithdrawAmountValidator
from settings.common import BOT_NAME
from database.bot_settings import get_or_create_bot_settings
from database.rates import get_all_rates
from database.state import States, get_state
from mixins.base import UserInputMixin
from triggers import Triggers

env = Environment(loader=FileSystemLoader('templates'))


class Expectations:  #  todo: this is not used yet anywhere
    EXPECT_CHECK_AMOUNT = Triggers.CHECK_AMOUNT
    EXPECT_BILL_AMOUNT = Triggers.BILL_AMOUNT


class RatesContext:
    async def get_rates(self):
        return await get_all_rates()


class BotSettingsContext:
    @property
    async def bot_settings(self):
        return await get_or_create_bot_settings()


class DefaultContext(RatesContext, BotSettingsContext):
    def __init__(self, user: dict, page: int) -> None:
        self.page = page
        self.user = user
        self.triggers = Triggers

    @staticmethod
    def format(value: Decimal, crypto: str) -> str:
        round_map = {
            'BTC': 8,
            'ETH': 6,
            'USDT': 2,
            'TRX': 7,
            'TON': 7
        }
        return str(round(value, round_map.get(crypto, 2)))
    
    async def render_template(self, template_name: str, ctx: Optional[dict] = None) -> str:
        template = env.get_template(template_name)
        return template.render(ctx or {})

    async def selected(self) -> dict:
        return await get_state(user_id=self.user['user_id'], key=States.SELECTED)

    async def ctx(self) -> dict:
        return {}

    def markup(self) -> list:
        return [[['Назад', Triggers.START]]]

    async def rm(self) -> InlineKeyboardMarkup:
        inline_keyboard = []
        for row in await self.markup():
            inline_keyboard.append([InlineKeyboardButton(text=button[0], callback_data=button[1]) for button in row])
        return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    async def pagination(self, buttons: list, trigger: str) -> list:
        bot_settings = await self.bot_settings
        per_page =bot_settings['pagination']['per_page']
        if len(buttons) > per_page:
            total_pages = (len(buttons) + per_page - 1) // per_page
            start_index = (self.page - 1) * per_page
            end_index = start_index + per_page
            buttons = buttons[start_index:end_index]

            pagination = [
                [f'·{page}·' if page == self.page else f'{page}', f'{trigger}|{page}']
                for page in range(1, total_pages + 1)
            ]
            if len(pagination) > 5:
                first = pagination[0]
                overflow = total_pages - self.page > 2
                last = [f'{total_pages} »' if overflow else str(total_pages), f'{trigger}|{total_pages}']
                middle = pagination[1 : len(pagination) - 1]
                if self.page < 4:
                    middle = middle[0:3]
                else:
                    if self.page > total_pages - 3:
                        middle = middle[-3:]
                        middle[0] = [f'‹ {middle[0][0]}', middle[0][1]]
                        first = [f'« {first[0]}', first[1]]
                    else:
                        middle = middle[self.page - 2 : self.page + 1]
                middle[-1] = [f'{middle[-1][0]} ›' if overflow else f'{middle[-1][0]}', middle[-1][1]]
                pagination = [first, *middle, last]
            buttons.append(pagination)
        return buttons


class StartContext(DefaultContext):
    async def ctx(self) -> dict:
        bot_settings = await self.bot_settings
        channel_link = bot_settings['links']['channel']
        chat_link = bot_settings['links']['chat']
        return {
            "channel_link": f"<a href='{channel_link}'>канал</a>",
            "chat_link": f"<a href='{chat_link}'>чат</a>",
        }


class UserInputContext(DefaultContext, UserInputMixin):
    async def _render_model_by_code(self, selected: list, trigger: str) -> str:
        base_ctx = {
            "wallet_currency": self.user['profile']['wallet_currency'],
            "bot_name": BOT_NAME
        }
        rates = await self.get_rates()
        instance, fiat_amount = await self.get_model_amount_in_fiat(rates=rates, code=selected[-1], trigger=trigger)
        template_map = {
            Triggers.CHECK: 'wallet/check.html',
            Triggers.BILL: 'wallet/bill.html',
        }
        ctx = {
            **base_ctx,
            "fiat_amount": fiat_amount,
        }
        if trigger == Triggers.CHECK:
            ctx['check'] = instance
        elif trigger == Triggers.BILL:
            ctx['bill'] = instance
        return await self.render_template(
            template_map[trigger],
            ctx=ctx
        )

    async def markup(self) -> list:
        selected = await self.selected()
        return [[['Назад', selected[-2] if len(selected) > 1 else Triggers.START]]]

    async def ctx(self) -> dict:
        selected = await self.selected()
        try:
            trigger = selected[-3]
        except IndexError:
            trigger = Triggers.START
        validator_cls = {
            Triggers.CREATE_CHECK: CheckAmountValidator,
            Triggers.CREATE_BILL: BillAmountValidator,
            Triggers.WITHDRAW: WithdrawAddressValidator,
        }.get(
            trigger
        )
        validator = validator_cls(self) if validator_cls else None
        if validator:
            text = await validator.validate(selected[-1])
        elif selected[-2] == Triggers.CHECK:
            text = await self._render_model_by_code(selected, Triggers.CHECK)
        elif selected[-2] == Triggers.BILL:
            text = await self._render_model_by_code(selected, Triggers.BILL)
        elif selected[-4] == Triggers.WITHDRAW:
            text = await WithdrawAmountValidator(self).validate(selected[-1])
        else:
            text = await self.render_template('errors/error.html', {})
        return {"text": text}
