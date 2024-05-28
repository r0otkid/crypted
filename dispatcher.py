import logging
import importlib
from typing import Callable, Awaitable, Any
from aiogram import Bot
from aiohttp import web
from aiogram.types import Update
from gettext import gettext as _

from database.keyboard import get_keyboard
from database.response import get_response
from database.state import States, get_state, set_state
from database.user import update_or_create_user
from database.user import get_user
from telegram import answer_callback_query, delete_last_message, send_message

class CustomDispatcher:
    def __init__(self):
        self.handlers = {}

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

    def register_handler(self, update_type: Any, handler: Callable[[Update], Awaitable[None]]):
        self.handlers[update_type] = handler

    async def handle_webhook(self, request: web.Request, bot: Bot):
        data = await request.json()
        update = Update(**data)
        await self.process_update(update, bot)
        return web.Response(status=200)

    async def set_webhook(self, bot, webhook_url):
        await bot.delete_webhook()
        await bot.set_webhook(webhook_url)


async def _handle_response(update: Update, bot: Bot, trigger: str) -> dict:
    async def _get_context(class_path) -> dict:
        module_name, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        return await cls(user=user).ctx()

    empty = _('Ответ не найден')
    user = await get_user(update=update)
    last = await get_state(user_id=user['user_id'], key=States.LAST_MESSAGE)
    if last:
        await delete_last_message(bot=bot, user=user, last=last)
    response_data = await get_response(trigger=trigger)
    if response_data:
        context = await _get_context(f"context.{response_data.get('context', 'base.DefaultContext')}")
        
        response_text = response_data.get('response', empty).format(**context)
        keyboard_id = response_data.get('keyboard_id')
        keyboard = await get_keyboard(keyboard_id) if keyboard_id else None
        message = await send_message(bot=bot, chat_id=user['user_id'], text=response_text, reply_markup=keyboard)
    else:
        message = await send_message(bot=bot, chat_id=user['user_id'], text=empty)
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
    user = await _handle_response(update, bot, callback_query.data)
    logging.info("Received callback query: %s from user %s" % (callback_query.data, user['user_id']))
    await answer_callback_query(callback_query_id=callback_query.id, bot=bot)
    return user