from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

async def delete_last_message(bot: Bot, user: dict, last: int):
    try:
        await bot.delete_message(chat_id=user['user_id'], message_id=last)
    except TelegramBadRequest:
        pass

async def answer_callback_query(bot: Bot, callback_query_id):
    try:
        await bot.answer_callback_query(callback_query_id=callback_query_id)
    except TelegramBadRequest:
        pass