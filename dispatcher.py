import json
import logging
import importlib
from datetime import datetime
from typing import Callable, Awaitable, Any, Optional
from aiogram import Bot
from aiogram.client.default import Default
from aiohttp import web
from aiogram.types import Update, InlineKeyboardMarkup
from gettext import gettext as _

from triggers import Triggers, get_all_triggers
from database.keyboard import get_keyboard
from database.response import get_response
from database.state import States, get_state, set_state
from database.user import update_or_create_user
from database.user import get_user
from telegram import answer_callback_query, delete_last_message, send_message


class CustomDispatcher:
    def __init__(self):
        self.handlers = {}

    def _custom_serializer(self, obj):
        """Сериализация типов данных json для распечатки в логах"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Default):
            return str(obj)
        raise TypeError(f'Type {type(obj)} not serializable')

    def _remove_none_values(self, data):
        """Очищает null значения в json для распечатки в логах"""
        if isinstance(data, dict):
            return {k: self._remove_none_values(v) for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            return [self._remove_none_values(item) for item in data if item is not None]
        else:
            return data

    def register_handler(self, update_type: Any, handler: Callable[[Update], Awaitable[None]]):
        self.handlers[update_type] = handler

    async def handle_webhook(self, request: web.Request, bot):
        data = await request.json()
        update = Update(**data)

        update_dict = update.model_dump()
        filtered_dict = self._remove_none_values(update_dict)

        formatted_json = json.dumps(filtered_dict, indent=4, default=self._custom_serializer)

        logging.info(f'Process update: {formatted_json}')

        await self.process_update(update, bot)
        return web.Response(status=200)

    async def set_webhook(self, bot, webhook_url):
        await bot.delete_webhook()
        await bot.set_webhook(webhook_url)

    async def process_update(self, update: Update, bot: Bot):
        if update.message:
            handler = self.handlers.get(update.message.__class__)
        elif update.callback_query:
            handler = self.handlers.get(update.callback_query.__class__)
        else:
            handler = None

        if handler:
            await update_or_create_user(update=update)
            await handler(update, bot)


async def _handle_response(update: Update, bot: Bot, trigger: str, page: int = 1) -> dict:
    async def _get_context(class_path) -> dict:
        module_name, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name) if hasattr(module, class_name) else None
        return await cls(user=user, page=page).ctx() if cls else {}

    async def _get_reply_markup(class_path) -> Optional[InlineKeyboardMarkup]:
        module_name, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name) if hasattr(module, class_name) else None
        return await cls(user=user, page=page).rm() if cls else None

    empty = _('Ответ не найден')

    user = await get_user(update=update)

    last = await get_state(user_id=user['user_id'], key=States.LAST_MESSAGE)
    if last:
        await delete_last_message(bot=bot, user=user, last=last)

    # заполняем цепочку триггеров
    await set_state(user_id=user['user_id'], key=States.LAST_TRIGGER, value=trigger)
    selected = await get_state(user_id=user['user_id'], key=States.SELECTED)

    if trigger in selected:
        index = selected.index(trigger)
        new_selected = selected[: index + 1]
    else:
        new_selected = selected + [trigger]

    await set_state(user_id=user['user_id'], key=States.SELECTED, value=new_selected)

    selected = new_selected

    # Обработка произвольного ввода пользователя
    all_triggers = get_all_triggers(Triggers)
    if trigger not in all_triggers:
        trigger = Triggers.USER_INPUT

    response_data = await get_response(trigger=trigger)

    if response_data:
        ctx_path = f"context.{response_data.get('context', 'base.DefaultContext')}"
        context = await _get_context(ctx_path)

        response_text = response_data.get('response', empty).format(**context)
        keyboard_id = response_data.get('keyboard_id')
        keyboard = await get_keyboard(keyboard_id, user) if keyboard_id else None
        if not keyboard:
            keyboard = await _get_reply_markup(ctx_path)
        message = await send_message(bot=bot, chat_id=user['user_id'], text=response_text, reply_markup=keyboard)
    else:
        message = await send_message(bot=bot, chat_id=user['user_id'], text=empty)

    if message:
        await set_state(user_id=user['user_id'], key=States.LAST_MESSAGE, value=message.message_id)
    return user


# Обработка сообщения
async def handle_message(update: Update, bot: Bot) -> dict:
    message = update.message
    user = await _handle_response(update, bot, message.text)
    logging.info("Received message: %s from user: %s" % (message.text, user['user_id']))
    return user


# Обработка callback-запроса
async def handle_callback_query(update: Update, bot: Bot) -> dict:
    callback_query = update.callback_query
    # важный момент: парсим тут нагрузку в виде номера страницы
    trigger = callback_query.data.split('|')[0] if '|' in callback_query.data else callback_query.data
    page = int(callback_query.data.split('|')[1]) if '|' in callback_query.data else 1
    user = await _handle_response(update, bot, trigger, page)
    logging.info("Received callback query: %s from user %s" % (callback_query.data, user['user_id']))
    await answer_callback_query(callback_query_id=callback_query.id, bot=bot)
    return user
