from typing import Optional
from aiogram import Bot, types
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


async def send_message(
    bot: Bot, chat_id: int, text: str, reply_markup: Optional[types.ReplyKeyboardMarkup] = None
) -> Optional[types.Message]:
    try:
        message = await bot.send_message(
            chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML', disable_web_page_preview=True
        )
    except TelegramBadRequest:
        message = None
    return message
