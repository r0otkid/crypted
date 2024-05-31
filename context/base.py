from typing import Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from jinja2 import Environment, FileSystemLoader
from context.validators.wallet import BillAmountValidator, CheckAmountValidator
from database.check import get_check_by_code
from database.state import States, get_state
from triggers import Triggers

env = Environment(loader=FileSystemLoader('templates'))


class Expectations:  #  todo: this is not used yet anywhere
    EXPECT_CHECK_AMOUNT = Triggers.CHECK_AMOUNT
    EXPECT_BILL_AMOUNT = Triggers.BILL_AMOUNT


class DefaultContext:
    def __init__(self, user: dict, page: int) -> None:
        self.page = page
        self.user = user
        self.triggers = Triggers

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
        per_page = 1  #  TODO: взять из настроек
        if len(buttons) > per_page:
            # Рассчитать количество страниц
            total_pages = (len(buttons) + per_page - 1) // per_page
            # Получить начальный и конечный индексы для текущей страницы
            start_index = (self.page - 1) * per_page
            end_index = start_index + per_page
            # Сделать срез
            buttons = buttons[start_index:end_index]

            # Создать кнопки пагинации
            pagination = [
                [f'·{page}·' if page == self.page else f'{page}', f'{trigger}|{page}']
                for page in range(1, total_pages + 1)
            ]
            if len(pagination) > 5:
                first = pagination[0]
                overflow = total_pages - self.page > 2
                last = [f'{total_pages} »' if overflow else str(total_pages), f'{trigger}|{total_pages}']
                middle = pagination[1:len(pagination) - 1]
                if self.page < 4:
                    middle = middle[0:3]
                else:
                    if self.page > total_pages - 3:
                        middle = middle[-3:]
                        middle[0] = [f'‹ {middle[0][0]}', middle[0][1]]
                        first = [f'« {first[0]}', first[1]]
                    else:
                        middle = middle[self.page - 2:self.page + 1]
                middle[-1] = [f'{middle[-1][0]} ›' if overflow else f'{middle[-1][0]}', middle[-1][1]]
                pagination = [first, *middle, last]
            buttons.append(pagination)
        return buttons

class StartContext(DefaultContext):
    async def ctx(self) -> dict:
        return {
            "channel_link": "<a href='https://ya.ru'>канал</a>",
            "chat_link": "<a href='https://ya.ru'>чат</a>",
        }


class UserInputContext(DefaultContext):
    async def markup(self) -> list:
        selected = await self.selected()
        return [[['Назад', selected[-2] if len(selected) > 1 else Triggers.START]]]

    async def ctx(self) -> dict:
        selected = await self.selected()
        try:
            trigger = selected[-3]
        except IndexError:
            trigger = Triggers.START
        validator_cls = {Triggers.CREATE_CHECK: CheckAmountValidator, Triggers.CREATE_BILL: BillAmountValidator}.get(
            trigger
        )
        validator = validator_cls(self) if validator_cls else None
        base_ctx = {
                "wallet_currency": "RUB",  # TODO: берем из профиля
                "bot_name": "Crawler_Robot"  #  TODO: берем из конфига
        }
        if validator:
            text = await validator.validate(selected[-1])
        elif selected[-2] == Triggers.CHECK:
            text = await self.render_template('wallet/check.html', {
                **base_ctx,
                "fiat_amount": 777,  #  TODO: посчитать по курсу
                "check": await get_check_by_code(selected[-1]),
            })
        elif selected[-2] == Triggers.BILL:
            text = await self.render_template('wallet/bill.html', {
                **base_ctx,
                "fiat_amount": 777,  #  TODO: посчитать по курсу
                "bill": await get_check_by_code(selected[-1]),
            })
        else:
            text = await self.render_template('errors/error.html', {})
        return {"text": text}
